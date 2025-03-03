#import os, sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))

"""BYD Battery Box Class"""

import logging
from datetime import datetime
from typing import Optional, Literal
import asyncio
import binascii
import json
import csv
import os
from .extmodbusclient import ExtModbusClient

from .bydbox_const import (
    INVERTER_LIST,
    LVS_INVERTER_LIST,
    HVL_INVERTER_LIST,

    APPLICATION_LIST,
    MODULE_TYPE,
    PHASE_LIST,
    WORKING_AREA,

    BMU_CALIBRATION,
    BMU_ERRORS,
    BMU_LOG_CODES,
    BMU_STATUS,

    BMS_ERRORS,
    BMS_LOG_CODES,
    BMU_LOG_ERRORS,
    BMU_LOG_WARNINGS,
    BMS_POWER_OFF,
    BMS_STATUS_ON,
    BMS_STATUS_OFF,
    BMS_WARNINGS,
    BMS_WARNINGS3,

    DATA_POINTS,
    MODULE_SPECS
)

_LOGGER = logging.getLogger(__name__)

class BydBoxClient(ExtModbusClient):
    """Async Modbus Client for BYD Battery Box"""

    initialized = False

    _bms_qty = 0
    _modules = 0
    _cells = 0 # number of cells per module
    _temps = 0 # number of temp sensors per module
    _bat_type = ''
    _new_logs = {}
    _b_cells_total = {}
    _min_response_delay = 0.2 # minimum delayin s after write register
    _retry_delay = 0.2

    data = {}
    log = {}

    def __init__(self, host: str, port: int, unit_id: int, timeout: int) -> None:
        """Init Class"""
        super(BydBoxClient, self).__init__(host = host, port = port, unit_id=unit_id, timeout=timeout, framer='rtu')

        self.data['unit_id'] = unit_id

        self._log_path = './custom_components/byd_battery_box/log/'
        self._log_csv_path = self._log_path + 'byd_log.csv'
        self._log_txt_path = self._log_path + 'byd.log'
        self._log_json_path = self._log_path + 'byd_log.json'

    def toggle_busy(func):
        async def wrapper(self, *args, **kwargs):
            if self.busy:
                _LOGGER.debug(f"skip {func.__name__} client busy") 
                return False
            self.busy = True
            error = None
            try:
                result = await func(self, *args, **kwargs)
            except Exception as e:
                _LOGGER.warning(f'Exception in wrapper {e}')
                error = e
            self.busy = False
            if not error is None:
                raise error
            return result
        return wrapper

    @toggle_busy
    async def init_data(self, close = False) -> bool:

        if not self._client.connected: await self._client.connect() 

        try:
            await self.update_info_data()
        except Exception as e:
            raise Exception(f"Error reading base info unit id: {self._unit_id}")

        try:
            await self.update_ext_info_data()
        except Exception as e:
            raise Exception(f"Error reading ext info unit id: {self._unit_id}")

        self.initialized = True
        if close: self.close()
        _LOGGER.debug(f"init done.")          
        return True

    def update_log_from_file(self) -> bool:
        if not os.path.exists(self._log_path):
            try:
                os.mkdir(self._log_path)
                _LOGGER.warning(f"log did not exist, created new log folder: {self._log_path}")  
                return False
            except Exception as e:
                _LOGGER.error(f'Failed to create log folder {self._log_path}')
                return False

        if os.path.isfile(self._log_json_path):
            try:
                with open(self._log_json_path, 'r') as openfile:
                    # Reading from json file
                    log = json.load(openfile)
            except Exception as e:
                _LOGGER.debug(f"Failed loading json log file {e}")   
                return False       
            #self.save_log_txt_file(log, append=False)
            self.log = log        
            self.data['log_entries'] = len(self.log)    
            self.data[f'log'] = self.get_log_list(20)
            self._update_balancing_cells_totals()
            self.save_log_csv_file()
            _LOGGER.debug(f"log entries loaded: {len(log)}")  

            #TODO update last_log per unit
            # last_log = logs[-1]
            # log = {'ts': ts.timestamp(), 'u': unit_id, 'c': code, 'data': hexdata}
            # last_log_id = self._get_unit_log_sensor_id(0)                
            # code_desc = self._get_log_code_desc(unit_id, code)
            # self.data[last_log_id] = f'{ts.strftime("%m/%d/%Y, %H:%M:%S")} {code} {code_desc}'
            return True
        
        return False

    @toggle_busy
    async def update_all_bms_status_data(self) -> bool:
        for bms_id in range(1, self._bms_qty + 1):
            if bms_id > 0:
                await asyncio.sleep(.2)
            try:
                result = await self.update_bms_status_data(bms_id)
            except Exception as e:
                _LOGGER.error(f"Error reading BMS status data {bms_id}", exc_info=True)
                return False
            if not result:
                #_LOGGER.debug(f"Failed updating data BMS status data {bms_id}", exc_info=True)
                return False
        return True   

    @toggle_busy
    async def update_all_log_data(self) -> bool:
        result = False
        self._new_logs = {}
        for device_id in range(self._bms_qty + 1):
            if device_id > 0:
                await asyncio.sleep(.2)
            try:
                result = await self.update_log_data(device_id)
            except Exception as e:
                _LOGGER.error(f"Unknown error reading log {self._get_device_name(device_id)} data", exc_info=True)
            if not result:
                _LOGGER.debug(f'Failed update log {self._get_device_name(device_id)} data')
                return False

        self.data[f'log'] = self.get_log_list(20)
        self._update_balancing_cells_totals()
        self.data['log_entries'] = len(self.log)    
        return True

    def _update_balancing_cells_totals(self) -> None:
        try:
            if len(self.log) == 0:
                # skip until logs are available
                return
            balancing_total = [0,0,0]
            b_cells_total = {}
            for k, log in self.log.items():
                if log['c'] == 17:
                    ts = datetime.fromtimestamp(log['ts'])
                    decoded = self.decode_bms_log_data(ts, 17, bytearray.fromhex(log['data']))
                    b_cells = decoded['b_cells']
                    unit_id = log['u']
                    balancing_total[unit_id] += 1
                    unit_b_cells_total = {}
                    if unit_id in b_cells_total.keys():
                        unit_b_cells_total = b_cells_total.get(unit_id)
                    for cell_id in b_cells:
                        if cell_id in unit_b_cells_total.keys():
                            unit_b_cells_total[cell_id] += 1
                        else:
                            unit_b_cells_total[cell_id] = 1
                    b_cells_total[unit_id] = unit_b_cells_total

            r1, r2 = None, None
            if not b_cells_total.get(1) is None:
                r1 = self._get_balancings_totals_per_module(b_cells_total.get(1))
            if not b_cells_total.get(2) is None:
                r2 = self._get_balancings_totals_per_module(b_cells_total.get(2))
            
            self.data['bms1_b_total'] = balancing_total[1]
            self.data['bms2_b_total'] = balancing_total[2]
            self.data['bms1_b_cells_total'] = r1
            self.data['bms2_b_cells_total'] = r2
        except Exception as e:
            _LOGGER.error(f'Unknown error calculation balancing totals {e}', exc_info=True)
        #_LOGGER.debug(f'balancing {balancing_total[1]} {self._b_cells_total.get(1)}')
        #_LOGGER.debug(f'balancing {balancing_total[2]} {self._b_cells_total.get(2)}')
        
    def _get_balancings_totals_per_module(self, t) -> list:
        r = []
        for m in range(self._modules):
            mct = []
            for c in range(self._cells):
                ct = t.get(str((m * self._cells) + c))
                if ct is None:
                    ct = 0
                mct.append(ct)
            r.append({'m': m, 'bct':mct})
        return r

    def _get_inverter_model(self,model,id) -> str:
        inverter = None
        if model == "LVS":                     
          inverter = LVS_INVERTER_LIST.get(id)
        elif model == "HVL":                                 
          inverter = HVL_INVERTER_LIST.get(id)
        else:  # HVM, HVS
          if id >= 0 and id <= 16:
            inverter = INVERTER_LIST[id]
        if inverter is None:
            inverter = f'Unknown: {id} {model}'
            _LOGGER.error(f"unknown inverter. model: {model} inverter id: {id}")
        return inverter
    
    async def update_info_data(self) -> bool:
        """start reading info data"""
        regs = await self.get_registers(address=0x0000, count=20)
        if regs is None:
            return False

        bmuSerial = self._client.convert_from_registers(regs[0:10], data_type = self._client.DATATYPE.STRING)[:-1]
        # 10-12 ?
        _LOGGER.debug(f'bmu reg 10-12: {regs[10:12]}')
        bmu_v_A_1, bmu_v_A_2 = self.convert_from_registers_int8(regs[12:13])
        bmu_v_B_1, bmu_v_B_2 = self.convert_from_registers_int8(regs[13:14])
        bms_v1, bms_v2 = self.convert_from_registers_int8(regs[14:15])
        bmu_area, bms_area = self.convert_from_registers_int8(regs[15:16])
        towers, modules = self.convert_from_registers_int4(regs[16:17])
        application_id, lvs_type_id = self.convert_from_registers_int8(regs[17:18])
        phase_id = self.convert_from_registers_int8(regs[18:19])[0]
        # 19-21 ?
        _LOGGER.debug(f'bmu reg 19-21: {regs[19:21]}')

        if bmuSerial.startswith('P03') or bmuSerial.startswith('E0P3'):
            # Modules in Serial
            bat_type = 'HV'
            if towers > 3:
                towers = 3
                _LOGGER.warning(f'HV towers set to 3, BMU reported {towers}.')
        elif bmuSerial.startswith('P02') or bmuSerial.startswith('P011'):
            # Modules in Paralel
            bat_type = 'LV'
            towers += 1 # start counting at 0?
            _LOGGER.warning(f'LV towers set to {towers}, BMU reported {towers-1}.')
        else:
            _LOGGER.error(f'Battery type HV/LV could not be determined. SN starts wtih: {bmuSerial[:4]} ')

        bmu_v_A = f'{bmu_v_A_1}.{bmu_v_A_2}'
        bmu_v_B = f'{bmu_v_B_1}.{bmu_v_B_2}'
        bms_v = f'{bms_v1}.{bms_v2}'   

        if bmu_area == 0:
            bmu_v = bmu_v_A
        else:
            bmu_v = bmu_v_B

        self.data['serial'] = bmuSerial
        #self.data['serial'] = "xxxxxxxxxxxxxxxxxxx"  # for screenshots
        self.data['bat_type'] = bat_type
        self.data['bmu_v_A'] = bmu_v_A
        self.data['bmu_v_B'] = bmu_v_B
        self.data['bmu_v'] = bmu_v
        self.data['bms_v'] = bms_v
        self.data['bmu_area'] = WORKING_AREA[bmu_area]
        self.data['bms_area'] = WORKING_AREA[bms_area]
        self.data['towers'] = towers       
        self.data['modules'] = modules       
        self._bms_qty = towers
        self._modules = modules
        self._bat_type = bat_type

        self.data['application'] = APPLICATION_LIST[application_id]
        self.data['lvs_type'] = lvs_type_id
        self.data['phase'] = PHASE_LIST[phase_id]

        return True

    async def update_ext_info_data(self) -> bool:
        """start reading info data"""
        regs = await self.get_registers(address=0x0010, count=2)
        if regs is None:
            return False

        inverter_id = self.convert_from_registers_int8(regs[0:1])[0]
        bat_type_id = self.convert_from_registers_int8(regs[1:2])[0]

        model, capacity_module, cells, sensors_t = 'NA', 0.0, 0, 0
        if self._bat_type == 'HV':
            if bat_type_id == 0:
                model = "HVL"
            elif bat_type_id == 1:
                model = "HVM"
            elif bat_type_id == 2:
                model = "HVS"
            else:
                _LOGGER.error(f'Unknown HV battery type {bat_type_id}')
        elif self._bat_type == 'LV':
            if bat_type_id == 0:
                model = "LVL" # Assumption
            elif bat_type_id == 2:
                model = "LVS"
            else:
                # LVS Lite, LV Flex, LV Flex Lite
                _LOGGER.error(f'Unknown LV battery type {bat_type_id}')

        specs = MODULE_SPECS.get(model)
        if not specs is None:
            capacity_module = specs['capacity']
            self._cells = specs['cells']
            self._temps = specs['sensors_t']

        capacity = self._bms_qty * self._modules * capacity_module

        self.data['inverter'] = self._get_inverter_model(model, inverter_id)
        self.data['model'] = model
        self.data['capacity'] = capacity
        self.data['sensors_t'] = self._cells
        self.data['cells'] = self._temps

        return True

    @toggle_busy
    async def update_bmu_status_data(self) -> bool:
        """start reading bmu status data"""
        regs = await self.get_registers(address=0x0500, count=21) # 1280
        if regs is None:
            _LOGGER.warning('update_bmu_status_data regs is None')
            return False

        soc = self._client.convert_from_registers(regs[0:1], data_type = self._client.DATATYPE.UINT16)
        max_cell_voltage = round(self._client.convert_from_registers(regs[1:2], data_type = self._client.DATATYPE.UINT16) * 0.01,2)
        min_cell_voltage = round(self._client.convert_from_registers(regs[2:3], data_type = self._client.DATATYPE.UINT16) * 0.01,2)
        soh = self._client.convert_from_registers(regs[3:4], data_type = self._client.DATATYPE.UINT16)
        current = round(self._client.convert_from_registers(regs[4:5], data_type = self._client.DATATYPE.INT16) * 0.1,1)
        bat_voltage = round(self._client.convert_from_registers(regs[5:6], data_type = self._client.DATATYPE.UINT16) * 0.01,2)
        max_cell_temp = self._client.convert_from_registers(regs[6:7], data_type = self._client.DATATYPE.INT16)
        min_cell_temp = self._client.convert_from_registers(regs[7:8], data_type = self._client.DATATYPE.INT16)
        bmu_temp = self._client.convert_from_registers(regs[8:9], data_type = self._client.DATATYPE.INT16)
        # 9-12 ?
        if regs[9:13] != [0, 792, 0, 0]:
            _LOGGER.debug(f'bmu status reg 9-12: {regs[9:13]} [0, 792, 0, 0]')
        errors = self._client.convert_from_registers(regs[13:14], data_type = self._client.DATATYPE.UINT16)
        param_t_v1, param_t_v2 = self.convert_from_registers_int8(regs[14:15]) 
        output_voltage = round(self._client.convert_from_registers(regs[16:17], data_type = self._client.DATATYPE.UINT16) * 0.01,2)
        # TODO: change to use standard pymodbus function once HA has been upgraded to later version
        charge_lfte = self.convert_from_registers(regs[17:19], data_type = self._client.DATATYPE.UINT32, word_order='little') * 0.1
        discharge_lfte = self.convert_from_registers(regs[19:21], data_type = self._client.DATATYPE.UINT32, word_order='little') * 0.1

        param_t_v = f"{param_t_v1}.{param_t_v2}"
        efficiency = round((discharge_lfte / charge_lfte) * 100.0,1)

        self.data['soc'] = soc
        self.data['max_cell_v'] = max_cell_voltage
        self.data['min_cell_v'] = min_cell_voltage
        self.data['soh'] = soh
        self.data['current'] = current
        self.data['bat_voltage'] = bat_voltage
        self.data['max_cell_temp'] = max_cell_temp
        self.data['min_cell_temp'] = min_cell_temp
        self.data['bmu_temp'] = bmu_temp
        self.data['errors'] =  self.bitmask_to_string(errors, BMU_ERRORS, 'Normal')    
        self.data['param_t_v'] = param_t_v
        self.data['output_voltage'] = output_voltage
        self.data['power'] = current * output_voltage
        self.data['charge_lfte'] = charge_lfte
        self.data['discharge_lfte'] = discharge_lfte
        self.data['efficiency'] = efficiency
        self.data[f'updated'] = datetime.now()

        return True
       
    async def update_bms_status_data(self, bms_id) -> bool:
        """start reading status data"""

        await self.write_registers(unit_id=self._unit_id, address=0x0550, payload=[bms_id,0x8100])
 
        response_reg = await self._wait_for_response(address = 0x0551)
        if not response_reg:
            return None

        regs = []
        for i in range(4):
            new_regs = await self.get_registers(address=0x0558, count=65)
            if new_regs is None:
                _LOGGER.error(f"Failed reading BMS {bms_id} status part {i}", exc_info=True)
                return False
            else:
                regs += new_regs

        if not len(regs) == 260:
            _LOGGER.error(f"unexpected number of BMS {bms_id} status regs: {len(regs)}")
            return False

        # skip 1st register with length
        max_voltage = round(self._client.convert_from_registers(regs[1:2], data_type = self._client.DATATYPE.INT16) * 0.001,3)
        if max_voltage > 5:
            _LOGGER.error(f"BMS {bms_id} unexpected max voltage {max_voltage}", exc_info=True)
            return False
        min_voltage = round(self._client.convert_from_registers(regs[2:3], data_type = self._client.DATATYPE.INT16) * 0.001,3)
        max_voltage_cell_module, min_voltage_cell_module = self.convert_from_registers_int8(regs[3:4])
        max_temp = self._client.convert_from_registers(regs[4:5], data_type = self._client.DATATYPE.INT16)
        min_temp = self._client.convert_from_registers(regs[5:6], data_type = self._client.DATATYPE.INT16)
        max_temp_cell_module, min_temp_cell_module = self.convert_from_registers_int8(regs[6:7])

        cell_balancing = []
        balancing_cells = 0
        for m in range(self._modules):
            flags = self._client.convert_from_registers(regs[7+m:7+m+1], data_type = self._client.DATATYPE.UINT16)
            bl = []
            for bit in range(16):
                #b = flags & (1>>bit)
                b = flags >> bit & 1
                #_LOGGER.debug(f'bit {b} {flags} {bit} {m}')
                balancing_cells += b 
                bl.append(b)
            cell_balancing.append({'m':m+1, 'b':bl})

        # TODO: change to use standard pymodbus function once HA has been upgraded to later version
        charge_lfte = self.convert_from_registers(regs[15:17], data_type = self._client.DATATYPE.UINT32, word_order='little') * 0.001
        discharge_lfte = self.convert_from_registers(regs[17:19], data_type = self._client.DATATYPE.UINT32, word_order='little') * 0.001
        # 20 ? 
        reg20 = self.convert_from_registers(regs[20:21], data_type = self._client.DATATYPE.UINT16) 
        reg20a, reg20b = self.convert_from_registers_int8(regs[3:4])
        _LOGGER.debug(f'bms {bms_id} reg 20: uint16 {reg20} int8 a {reg20a} b {reg20b}')

        bat_voltage = round(self._client.convert_from_registers(regs[21:22], data_type = self._client.DATATYPE.INT16) * 0.1,2)
        # 22 ?
        if regs[22] != 0:
            _LOGGER.debug(f'bms {bms_id} reg 22: {regs[22]} 0')
        # 23 ? Switch State ?
        if regs[23] != 1560:
            _LOGGER.debug(f'bms {bms_id} reg 23: {regs[23]} 1560')

        output_voltage = round(self._client.convert_from_registers(regs[24:25], data_type = self._client.DATATYPE.INT16) * 0.1,2)
        soc = round(self._client.convert_from_registers(regs[25:26], data_type = self._client.DATATYPE.INT16) * 0.1,2)
        soh = self._client.convert_from_registers(regs[26:27], data_type = self._client.DATATYPE.INT16)
        current = round(self._client.convert_from_registers(regs[27:28], data_type = self._client.DATATYPE.INT16) * 0.1,2)
        warnings1 = self._client.convert_from_registers(regs[28:29], data_type = self._client.DATATYPE.UINT16)
        warnings2 = self._client.convert_from_registers(regs[29:30], data_type = self._client.DATATYPE.UINT16)
        warnings3 = self._client.convert_from_registers(regs[30:31], data_type = self._client.DATATYPE.UINT16)
        # 31-47 ?
        if regs[31:42] != [6659, 7683, 256, 20528, 13104, 21552, 12848, 23090, 12848, 14129, 12593]:
            _LOGGER.debug(f'bms {bms_id} reg 31-42: {regs[31:42]} [6659, 7683, 256, 20528, 13104, 21552, 12848, 23090, 12848, 14129, 12593, 13619, 12920, 30840, 30840, 270, 270]')
        if regs[42:44] != [13619, 12920]:
            _LOGGER.debug(f'bms {bms_id} reg 42-44: {regs[42:44]} [13619, 12920]')                           
        if regs[44:48] != [30840, 30840, 270, 270]:
            _LOGGER.debug(f'bms {bms_id} reg 44-48: {regs[44:48]} [30840, 30840, 270, 270]')                           

        errors = self._client.convert_from_registers(regs[48:49], data_type = self._client.DATATYPE.UINT16)
        all_cell_voltages = []
        cell_voltages= [] # list of dict

        regs_voltages = regs[49:65] + regs[66:130] + regs[131:180]
        regs_temps = regs[180:195] + regs[196:213] 

        all_cell_temps = []
        cell_temps = [] # list of dict

        temp_parts = 0
        if self._temps > 0:
            temp_parts = round(self._temps/2)

        for m in range(self._modules):
            values = []
            for i in range(self._cells):
                 voltage = self._client.convert_from_registers(regs_voltages[i+m*16:i+m*16+1], data_type = self._client.DATATYPE.INT16)
                 values.append(voltage)
            all_cell_voltages += values
            cell_voltages.append({'m':m+1, 'v':values})
            values = []
            for i in range(temp_parts):
                values += self.convert_from_registers_int8(regs_temps[i+m*4:i+m*4+1])
            all_cell_temps += values
            cell_temps.append({'m':m+1, 't':values})

        # calculate quantity cells balancing
        #balancing_cells = 0
        #for cell in cell_flags:
        #   if cell['f'] & 1 == 1:
        #      balancing_cells += 1

        efficiency = round((discharge_lfte / charge_lfte) * 100.0, 1)

        avg_cell_voltage = round(sum(all_cell_voltages) / len(all_cell_voltages) * 0.001, 3)
        avg_cell_temp = round(sum(all_cell_temps) / len(all_cell_temps),1)

        warnings_list = self.bitmask_to_strings(warnings1, BMS_WARNINGS) + self.bitmask_to_strings(warnings2, BMS_WARNINGS) + self.bitmask_to_strings(warnings3, BMS_WARNINGS3)
        warnings = self.strings_to_string(strings=warnings_list, default='Normal', max_length=255)

        updated = datetime.now()

        self.data[f'bms{bms_id}_max_c_v'] = max_voltage
        self.data[f'bms{bms_id}_min_c_v'] = min_voltage
        self.data[f'bms{bms_id}_max_c_v_id'] = max_voltage_cell_module
        self.data[f'bms{bms_id}_min_c_v_id'] = min_voltage_cell_module
        self.data[f'bms{bms_id}_max_c_t'] = max_temp
        self.data[f'bms{bms_id}_min_c_t'] = min_temp
        self.data[f'bms{bms_id}_max_c_t_id'] = max_temp_cell_module
        self.data[f'bms{bms_id}_min_c_t_id'] = min_temp_cell_module
        self.data[f'bms{bms_id}_balancing_qty'] = balancing_cells
        self.data[f'bms{bms_id}_soc'] = soc
        self.data[f'bms{bms_id}_soh'] = soh
        self.data[f'bms{bms_id}_current'] = current
        self.data[f'bms{bms_id}_bat_voltage'] = bat_voltage
        self.data[f'bms{bms_id}_output_voltage'] = output_voltage
        self.data[f'bms{bms_id}_charge_lfte'] = charge_lfte
        self.data[f'bms{bms_id}_discharge_lfte'] = discharge_lfte
        self.data[f'bms{bms_id}_efficiency'] = efficiency

        self.data[f'bms{bms_id}_warnings'] = warnings
        self.data[f'bms{bms_id}_errors'] = self.bitmask_to_string(errors, BMS_ERRORS, 'Normal')    
        self.data[f'bms{bms_id}_cell_balancing'] = cell_balancing
        self.data[f'bms{bms_id}_cell_voltages'] = cell_voltages
        self.data[f'bms{bms_id}_avg_c_v'] = avg_cell_voltage

        self.data[f'bms{bms_id}_cell_temps'] = cell_temps
        self.data[f'bms{bms_id}_avg_c_t'] = avg_cell_temp

        self.data[f'bms{bms_id}_updated'] = updated

        return True
    
    async def update_log_data(self, unit_id, log_depth = 1) -> bool:
        entries = 0
        if log_depth == 1: 
            update_last = True 
        else: 
            update_last = False
        
        for i in range(log_depth):
            new = await self._read_log_data_unit(unit_id, update_last=update_last)
            if new is None: 
                return False
            entries += new
            if log_depth > 1:
                if new < 20:
                    break
                _LOGGER.warning(f'...updating {self._get_device_name(unit_id)} log {entries} entries.')
        if log_depth > 1:                
            _LOGGER.warning(f'Finished updating {self._get_device_name(unit_id)} log; found {entries} log entries.')
        return True
   
    async def _wait_for_response(self, address, ready_response = 0x8801):
        response_reg = 0
        timeout = 5
        dt = 0
        #j = 0
        #start = datetime.now()
        await asyncio.sleep(self._min_response_delay)
        while response_reg != ready_response and dt < timeout: # wait for the response
            await asyncio.sleep(self._retry_delay)
            dt += self._retry_delay
            try:
                data = await self.read_holding_registers(unit_id=self._unit_id, address=address, count=1)
                if not data is None:
                    if not data.isError():
                        response_reg = data.registers[0]
                    else:
                        _LOGGER.debug(f"error while waiting for response {address} {data}", exc_info=True)
            except Exception as e:
                _LOGGER.debug(f"error while waiting for response {address}", exc_info=True)
            #j += 1
        if response_reg == ready_response:
            #_LOGGER.debug(f'waiting for ready response took {j} pings and {(datetime.now() - start).total_seconds()}s {dt}')
            return True
        elif dt < timeout:
            _LOGGER.error(f"unexpected wait response {response_reg}", exc_info=True)
            return False
        else:
            _LOGGER.error(f"wait for response timeout. {address}", exc_info=True)
            return False
 
    async def _read_log_data_unit(self, unit_id, update_last = True) -> int:
        """start reading log data"""
        #_LOGGER.debug(f'start updating log data {self._get_device_name(unit_id)} update_last: {update_last}')
        try:
            await self.write_registers(unit_id=self._unit_id, address=0x05a0, payload=[unit_id,0x8100])
        except Exception as e:
            _LOGGER.error(f"read {self._get_device_name(unit_id)} log data error when requesting data", exc_info=True)
            return None

        response_reg = await self._wait_for_response(address = 0x05A1)
        if not response_reg:
            return None

        regs = []
        for i in range(5):
            new_regs = await self.get_registers(address=0x05A8, count=65)
            if new_regs is None:
                _LOGGER.error(f"Failed reading {self._get_device_name(unit_id)} log part: {i}", exc_info=True)
                return None
            else:
                regs += new_regs[1:] # skip first byte 

        if len(regs) == 0 or not len(regs) == 320:
            _LOGGER.error(f"Unexpected number of {self._get_device_name(unit_id)}  log regs: {len(regs)}")
            return None    
        
        entries = 0
        ts:datetime = None
        for i in range(0,20):
            sub_regs=regs[i*15:i*15+15]

            data = bytearray()
            data.append(sub_regs[3] & 0xFF)
            for reg in sub_regs[4:]:
                data.append(reg >> 8 & 0xFF)
                data.append(reg & 0xFF)

            code, year = self.convert_from_registers_int8(sub_regs[0:1])
            month, day = self.convert_from_registers_int8(sub_regs[1:2])                 
            hour, minute = self.convert_from_registers_int8(sub_regs[2:3])              
            second, dummy = self.convert_from_registers_int8(sub_regs[3:4])

            if year == 0 and month == 0 and day == 0 and code == 0:
                _LOGGER.debug(f'Reached end: {i} {year}-{month}-{day} {hour}:{minute}:{second} code: {code}')
                break 
            if year in [255]:
                _LOGGER.error(f'Invalid year in log entry: {i} {year}-{month}-{day} {hour}:{minute}:{second} code: {code}')
                break 

            if month in [0,13]:
                _LOGGER.warning(f'Invalid month in log entry: {i} {year}-{month}-{day} {hour}:{minute}:{second} code: {code}')
                month = 1
            if day == 0:
                _LOGGER.warning(f'Invalid day in log entry: {i} {year}-{month}-{day} {hour}:{minute}:{second} code: {code}')
                day = 1

            try:
                year += 2000                 
                ts:datetime = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
            except Exception as e:
                _LOGGER.error(f'Failed to derive log timestamp entry: {i} {year}-{month}-{day} {hour}:{minute}:{second} code: {code} exception: {e}')
                break
            
            k = f'{ts.strftime("%Y%m%d %H:%M:%S")}-{code}-{unit_id}' 
            entries += 1
            #_LOGGER.debug(f'log {i} {k}')

            if not k in self.log.keys():
                hexdata = binascii.hexlify(data).decode('ascii')
                entry = {'ts': ts.timestamp(), 'u': unit_id, 'c': code, 'data': hexdata}
                self._new_logs[k] = entry
                self.log[k] = entry

            if update_last and i==0:
                last_log_id = self._get_unit_log_sensor_id(unit_id)                
                code_desc = self._get_log_code_desc(unit_id, code)
                self.data[last_log_id] = f'{ts.strftime("%m/%d/%Y, %H:%M:%S")} {code} {code_desc}'

        self.data['log_count'] = len(self.log)        

        return entries

    def _get_unit_log_sensor_id(self, unit_id) -> str:    
        if unit_id == 0:
            last_log_id = 'bmu_last_log'      
        else:
            last_log_id = f'bms{unit_id}_last_log' 
        return last_log_id    

    def _get_device_name(self, device_id) -> str:    
        if device_id == 0:
            unit = 'BMU'
        else:
            unit = f'BMS {device_id}'
        return unit    

    def _get_log_code_desc(self, unit_id, code)  -> str:
        if unit_id == 0:
            code_desc = self.get_value_from_dict(BMU_LOG_CODES, code, 'Not available')
        else:
            code_desc = self.get_value_from_dict(BMS_LOG_CODES, code, 'Not available')
        return code_desc

    def save_log_entries(self, append=True) -> None:
        # if append:
        #     self.save_log_txt_file(self._new_logs, append=True)
        # else:
        #     self.save_log_txt_file(self.log)
        self.log = dict(sorted(self.log.items()))
        self.save_log_csv_file()
        self.save_log_json_file()

        _LOGGER.debug(f'Saved {len(self._new_logs)} new log entries. Total: {len(self.log)}')
        return True

    def save_log_json_file(self) -> None:
        #log_s = dict(sorted(log.items()))
        with open(self._log_json_path, "w") as outfile:
            json.dump(self.log, outfile, indent=1, sort_keys=False, default=str)

    def save_log_txt_file(self, log:dict, append=True) -> None:
        if append:
            write_type = 'a'
        else:
            write_type = 'w'
        with open(self._log_txt_path, write_type) as myfile:
            for k, entry in self.log.items():
                unit_id, unit_name, ts, code, data  = self.split_log_entry(entry)
                code_desc, decoded = self.decode_log_data(unit_id, ts, code, data)
                detail = decoded['desc']
                line = f'{ts.strftime("%Y%m%d %H:%M:%S")} {unit_name} {code} {code_desc} {detail}\n' 
                myfile.write(line)

    def save_log_csv_file(self) -> None:
        with open(self._log_csv_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['ts', 'unit','code','description','detail','data'])
            
            for k, entry in self.log.items():
                unit_id, unit_name, ts, code, data  = self.split_log_entry(entry)
                code_desc, decoded = self.decode_log_data(unit_id, ts, code, data)
                detail = decoded['desc']
                log_list = [ts.strftime("%Y%m%d %H:%M:%S"), unit_name, code, code_desc, detail, binascii.hexlify(data).decode('ascii')]
                writer.writerow(log_list)

    def split_log_entry(self, log:dict):
        unit_id = int(log['u'])
        unit_name = self._get_device_name(unit_id)
        code = int(log['c'])
        ts = datetime.fromtimestamp(log['ts'])
        data = bytearray.fromhex(log['data'])

        return unit_id, unit_name, ts, code, data 

    def get_log_list(self, max_length) -> list:
        logs = sorted(self.log.items(), reverse=True)
        log_list = []
        for k, log in logs[:max_length]:
            unit_id, unit_name, ts, code, data = self.split_log_entry(log)
            code_desc, decoded = self.decode_log_data(unit_id, ts, code, data)
            detail = decoded.get('desc')
            hexdata = log['data']
            decoded.pop('desc')
            log_list.append({'ts': ts, 'u': unit_name, 'c': code, 'd': code_desc, 'data': decoded, 'detail': detail, 'data': hexdata})

        return log_list

    def decode_log_data(self, unit_id:int, ts:datetime, code:int, data:bytearray):
        decoded = {}
        if unit_id == 0:
            code_desc = self.get_value_from_dict(BMU_LOG_CODES, code, 'Not available')
            decoded = self.decode_bmu_log_data(ts, code, data)
        else:
            code_desc = self.get_value_from_dict(BMS_LOG_CODES, code, 'Not available')
            decoded = self.decode_bms_log_data(ts, code, data)

        if len(decoded)>0:
            decoded['desc'] = self.log_data_to_str(decoded)
        else:
            decoded['desc'] = f'Not decoded: {binascii.hexlify(data).decode('ascii')}'

        return code_desc, decoded

    def decode_bmu_log_data(self, ts:datetime, code:int, data:bytearray) -> dict:
        datapoints = {}

        if code == 0:
            datapoints['bootl'] = data[0]
            if data[1] == 0:
                datapoints['exec'] = 'A'
            elif data[1] == 1:
                datapoints['exec'] = 'B'
            else:
                datapoints['exec'] = data[1]
            datapoints['firmware_v'] = f"{data[2]:d}" + "." + f"{data[3]:d}" 
        elif code == 1:
            if data[0] == 0:
                datapoints['switchoff'] = '0' 
            elif data[0] == 1:
                datapoints['switchoff'] = 'LED button' 
            else:
                datapoints['switchoff'] = data[0] 
        elif code == 2:
            if data[0] == 0:
                event = 'Error/Warning cleared'
            else:            
                error_code = data[1]
                if error_code != 23:
                    error = self.get_value_from_dict(BMU_LOG_ERRORS, error_code, 'Undefined')
                    event = f'Error; {error.lower()}'
                else:
                    warnings = int(data[2] * 0x100 + data[3])
                    warnings_list = self.bitmask_to_strings(warnings, BMU_LOG_WARNINGS)
                    event = f'Warning; {self.strings_to_string(warnings_list).lower()}'

            datapoints['event'] = event
            datapoints['c_max_v'] = self.convert_from_byte_uint16(data,4)
            datapoints['c_min_v'] = self.convert_from_byte_uint16(data,6)
            datapoints['bat_max_t'] = data[8]
            datapoints['bat_min_t'] = data[9]
            datapoints['bat_v'] =  self.calculate_value(self.convert_from_byte_uint16(data,10), -1, 1) 
            datapoints['soc'] = data[12]                
            datapoints['soh'] = data[13]  
        elif code == 32:
            datapoints['p_status'] = self.get_value_from_dict(BMU_STATUS, data[1], 'NA')
            datapoints['n_status'] = self.get_value_from_dict(BMU_STATUS, data[0], 'Undefined')
        elif code == 34:
            datapoints['firmware_v'] = f"{data[1]:d}" + "." + f"{data[2]:d}" 
            datapoints['mcu'] = data[4]
        elif code == 35:
            datapoints['firmware_v'] = f"{data[1]:d}" + "." + f"{data[2]:d}" 
            datapoints['mcu'] = data[4]
        elif code == 36:
            running_time = data[0] * 0x01000000 + data[1] * 0x00010000 + data[2] * 0x00000100 + data[3]
            datapoints['rtime'] = running_time
            datapoints['bmu_qty_c'] = data[4]
            datapoints['bmu_qty_t'] = data[5]
            datapoints['c_max_v'] = self.convert_from_byte_uint16(data,6)
            datapoints['c_min_v'] = self.convert_from_byte_uint16(data,8)
            datapoints['c_max_t'] = data[10]
            datapoints['c_min_t'] = data[11]
            datapoints['out_a'] = self.calculate_value(self.convert_from_byte_int16(data,12), -1, 1)
            datapoints['out_v'] = self.calculate_value(self.convert_from_byte_uint16(data,14), -1, 1)
            datapoints['acc_v'] = self.calculate_value(self.convert_from_byte_uint16(data,16), -1, 1)
            datapoints['bms_addr'] = data[18]
            datapoints['m_type'] = self.get_value_from_dict(MODULE_TYPE, data[19], 'Undefined')
            datapoints['m_qty'] = data[20]
        elif code == 38:
            datapoints['max_charge_a'] = self.calculate_value(self.convert_from_byte_int16(data,0), -1, 1)
            datapoints['max_discharge_a'] = self.calculate_value(self.convert_from_byte_int16(data,2), -1, 1)
            datapoints['max_charge_v'] = self.calculate_value(self.convert_from_byte_int16(data,4), -1, 1)
            datapoints['max_discharge_v'] = self.calculate_value(self.convert_from_byte_int16(data,6), -1, 1)
            datapoints['status'] = [self.get_value_from_dict(BMU_STATUS, data[8], 'Undefined')]
            datapoints['bat_t'] = data[9]
            datapoints['inverter'] = INVERTER_LIST[data[10]]
            datapoints['bms_qty'] = data[11]
        elif code == 40:
            datapoints['firmware_n1']  = data[0]    
            datapoints['firmware_v1']  = f"{data[1]:d}" + "." + f"{data[2]:d}"
            datapoints['firmware_n2']  = data[3]    
            datapoints['firmware_v2']  = f"{data[4]:d}" + "." + f"{data[5]:d}"
            if data[6] != 0xFF:
                datapoints['firmware_n3']  = data[6]    
                datapoints['firmware_v3']  = f"{data[7]:d}" + "." + f"{data[8]:d}"
        elif code == 41:
            # ?
            pass
        elif code == 45:
            #status = self.get_value_from_dict(BMU_STATUS, data[0], 'Undefined')
            datapoints['status'] = f'{data[0]}'
            # 0: 0-1
            # 1: 0
            # 2: 0-1
            # 3: x02
            datapoints['out_v'] =  self.calculate_value(self.convert_from_byte_uint16(data,4), -1, 1) 
            datapoints['bat_v'] =  self.calculate_value(self.convert_from_byte_uint16(data,6), -1, 1) 
            # 8: 00
            # 9: 00
            datapoints['soc_a'] = self.calculate_value(self.convert_from_byte_uint16(data,10), -1, 1)
            datapoints['soc_b'] = self.calculate_value(self.convert_from_byte_uint16(data,12), -1, 1)
        elif code == 101:
            if data[0] == 0:
                datapoints['bms_updt'] = 'A'
            else:
                datapoints['bms_updt'] = 'A'
            datapoints['firmware_v'] = f"{data[1]:d}" + "." + f"{data[2]:d}" 
        elif code == 102:
            if data[0] == 0:
                datapoints['bms_updt'] = 'A'
            else:
                datapoints['bms_updt'] = 'A'
            datapoints['firmware_v'] = f"{data[1]:d}" + "." + f"{data[2]:d}" 
        elif code == 103:
            datapoints['firmware_n1']  = data[0]    
            datapoints['firmware_v1']  = f"{data[1]:d}" + "." + f"{data[2]:d}"
            datapoints['firmware_n2']  = data[3]    
            datapoints['firmware_v2']  = f"{data[4]:d}" + "." + f"{data[5]:d}"
        elif code == 105:
            if (data[0] == 0) or (data[0] == 1) or (data[0] == 2):
               # BMU Parameters table update
                #datapoints['pt_u'] = ''
                pass
            else:
                # ?
                pass
            datapoints['pt_v'] = f"{data[1]:d}" + "." + f"{data[2]:d}"
        elif code == 111:            
            datapoints['dt_cal'] = self.get_value_from_dict(BMU_CALIBRATION, data[0], 'Undefined')
        elif code == 118:
            status = self.get_value_from_dict(BMU_STATUS, data[0], 'Undefined')
            datapoints['status'] = [status]
            if status != 'Undefined':
                datapoints['env_min_t'] = data[1]                
                datapoints['env_max_t'] = data[2]                
                datapoints['soc'] = data[3]                
                datapoints['soh'] = data[4]                
                datapoints['bat_t'] = data[5]
                datapoints['bat_v'] = self.calculate_value(self.convert_from_byte_uint16(data,6), -1, 1) 
                datapoints['c_max_v'] = self.convert_from_byte_uint16(data,8)
                datapoints['c_min_v'] = self.convert_from_byte_uint16(data,10)
                datapoints['bat_max_t'] = data[13]
                datapoints['bat_min_t'] = data[15]
 
        return datapoints

    def decode_bms_log_data(self, ts:datetime, code:int, data:bytearray) -> dict:
        datapoints = {}

        if code == 0:
            datapoints['bootl'] = data[0]
            if data[1] == 0:
                datapoints['exec'] = 'A'
            elif data[1] == 2:
                datapoints['exec'] = 'B'
            else:
                datapoints['exec'] = data[1]
            datapoints['firmware_v'] = f"{data[3]:d}" + "." + f"{data[4]:d}" 
        elif code == 1:
            datapoints['power_off'] =self.get_value_from_dict(BMS_POWER_OFF, data[1], default='NA')

            if data[2] == 0:
                datapoints['section'] = 'A'
            elif data[2] == 1:
                datapoints['section'] = 'B'
            else:
                datapoints['section'] = data[2]

            datapoints['firmware_v']  = f"{data[3]:d}" + "." + f"{data[4]:d}"
        elif code in [2,3,4,5,6,7,9,10,11,13,14,16,19,20,21]:            
            warnings1 = int(data[1] * 0x100 + data[0])
            warnings2 = int(data[3] * 0x100 + data[2])
            warnings3 = int(data[5] * 0x100 + data[4])
            warnings_list = self.bitmask_to_strings(warnings1, BMS_WARNINGS) + self.bitmask_to_strings(warnings2, BMS_WARNINGS) + self.bitmask_to_strings(warnings3, BMS_WARNINGS3)
            datapoints['warnings'] = warnings_list

            errors = int(data[7] * 0x100 + data[6])
            errors_list = self.bitmask_to_strings(errors, BMS_ERRORS)
            datapoints['errors'] = errors_list

            status = int(data[8])
            if (status % 2) == 1:
                status_list = self.bitmask_to_strings(status, BMS_STATUS_OFF)            
            else:
                status_list = self.bitmask_to_strings(status, BMS_STATUS_ON)
            datapoints['status'] = status_list

            if code == 9:
                datapoints['bat_idle'] = data[9]
                datapoints['target_soc'] = data[10]
            elif code == 20:
                datapoints['bmu_serial_v1'] = data[9]
                datapoints['bmu_serial_v2'] = data[10]
            else:
                datapoints['soc'] = data[9]
                datapoints['soh'] = data[10]
                datapoints['bat_v'] = self.calculate_value(self.convert_from_byte_uint16(data,11,'LE'), -1, 1)
                datapoints['out_v'] = self.calculate_value(self.convert_from_byte_uint16(data,13,'LE'), -1, 1)
                datapoints['out_a'] = self.calculate_value(self.convert_from_byte_int16(data,15,'LE'), -1, 1)

            if code == 21:
                datapoints['c_max_v_n'] = data[17]
                datapoints['c_min_v_n'] = data[18]
                datapoints['c_max_t_n'] = data[20]
                datapoints['c_min_t_n'] = data[21]
            else:
                datapoints['c_max_v'] = self.convert_from_byte_uint16(data,17,'LE')
                datapoints['c_min_v'] = self.convert_from_byte_uint16(data,19,'LE')
                datapoints['c_max_t'] = data[21]
                datapoints['c_min_t'] = data[22]
        elif code in [17,18]:
            if code == 17:
                bc = []
                i = 0
                for j in range(20):  
                    b = int(data[j])
                    for bit in range(8):
                        if b >> bit & 1:
                            bc.append(str(i))
                        i += 1
                datapoints['b_cells'] = bc

            c_min_v = self.convert_from_byte_uint16(data,21,'LE')
            datapoints['c_min_v'] = c_min_v
        elif code in [101,102]:
            if data[0] == 0:
                datapoints['area'] = 'A'
            else:
                datapoints['area'] = 'B'
            datapoints['firmware_p']  = f"{data[2]:d}" + "." + f"{data[1]:d}"
            datapoints['firmware_n']  = f"{data[4]:d}" + "." + f"{data[3]:d}"
        elif code == 105:
            x = self.convert_from_byte_uint16(data, 0, type='LE')
            y = self.convert_from_byte_uint16(data, 2, type='LE')
#            datapoints['threshold']  = f"{x:d}" + "." + f"{y:d}"
            datapoints['pt_v']  = f"{x:d}" + "." + f"{y:d}"
        elif code == 106:
            datapoints['sn_change'] = 1
        elif code == 111:
            try:
                nt = datetime(year=data[0]+2000, month=data[1], day=data[2], hour=data[3], minute=data[4], second=data[5])
                datapoints['nt'] = nt
            except Exception as e:
                _LOGGER.error(f'Failed to convert to datetime {data[0]} {data[1]} {data[2]} {data[3]} {data[4]} {data[5]} {e}')
            #datapoints['dt'] = (ts - nt).total_seconds()

        return datapoints

    def log_data_to_str(self, data) -> str:
        strings = []
        for dp, v in data.items():
            dp_config = DATA_POINTS.get(dp)
            if not dp_config is None:
                s = f"{dp_config['label']}: "
                t = dp_config.get('type')
                if t in ['nlist','slist']:
                    if len(v) > 0:
                        if t == 'slist':
                            s += ', '.join(v)
                        else:
                            s += ','.join(v)                        
                    else:
                        s += '-'
                elif t == 's': # string
                    s = dp_config['label'].replace('{v}', f'{v}')
                else: # 'n' numeric
                    s += f"{v}"
                    unit = dp_config.get('unit')
                    if len(unit) > 0:
                        s += f" {unit}"
                strings.append(s)
            else:
                _LOGGER.error(f'Datapoint {dp} not defined')
        return f"{'. '.join(strings)}."