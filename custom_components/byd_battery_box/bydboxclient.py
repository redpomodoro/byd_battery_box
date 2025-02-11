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
)

_LOGGER = logging.getLogger(__name__)

class BydBoxClient(ExtModbusClient):
    """Hub for BYD Battery Box Interface"""

    def __init__(self, host: str, port: int, unit_id: int, timeout: int) -> None:
        """Init hub."""
        super(BydBoxClient, self).__init__(host = host, port = port, unit_id=unit_id, timeout=timeout, framer='rtu')

        self.initialized = False

        self._bms_qty = 0
        self._modules = 0
        self._cells = 0 # number of cells per module
        self._temps = 0 # number of temp sensors per module
        self._new_logs = {}
        self._b_cells_total = {}

        self.data = {}
        self.data['unit_id'] = unit_id
        self.log = {}

        self._log_path = './custom_components/byd_battery_box/log/'
        self._log_csv_path = self._log_path + 'byd_logs.csv'
        self._log_txt_path = self._log_path + 'byd.log'
        self._log_json_path = self._log_path + 'byd_logs.json'

    async def init_data(self, close = False, read_status_data = False):
        result = False

        await self.connect()
        try: 
            retries = 0
            result = await self.update_info_data()
            while result==False and retries<4:
                await asyncio.sleep(.1)
                result = await self.update_info_data()
                retries += 1
        except Exception as e:
            _LOGGER.error(f"Error reading base info {self._host}:{self._port} unit id: {self._unit_id}", exc_info=True)
            raise Exception(f"Error reading base info unit id: {self._unit_id}")

        if result == False:
            _LOGGER.error(f"Error reading info {self._host}:{self._port} unit id: {self._unit_id}")

        try:
            result = await self.update_ext_info_data()
        except Exception as e:
            _LOGGER.error(f"Error reading ext info data", exc_info=True)
            raise Exception(f"Error reading ext info unit id: {self._unit_id}")

        if read_status_data:
            try:
                result = await self.update_bmu_status_data()
            except Exception as e:
                _LOGGER.error(f"Error reading status data", exc_info=True)

            result = await self.update_all_bms_status_data()

        if close:
            self.close()
        self.initialized = True

        _LOGGER.debug(f"init done. data: {self.data}")          

        return True

    def update_logs_from_file(self) -> bool:

        if not os.path.exists(self._log_path):
            os.mkdir(self._log_path)
            _LOGGER.warning(f"log did not exist, created new log folder: {self._log_path}")  
            return False

        if os.path.isfile(self._log_json_path):
            try:
                with open(self._log_json_path, 'r') as openfile:
                    # Reading from json file
                    logs = json.load(openfile)
            except Exception as e:
                _LOGGER.debug(f"Failed loading json log file {e}")   
                return False       
            #self.save_log_txt_file(logs, append=False)
            self.save_log_csv_file(logs)
            self.log = logs        
            self._update_balancing_cells_totals()
            _LOGGER.debug(f"logs entries loaded: {len(logs)}")  

            #self.data['log_count'] = len(self.log)    
            # last_log = logs[-1]
            # log = {'ts': ts.timestamp(), 'u': unit_id, 'c': code, 'data': hexdata}
            # last_log_id = self._get_unit_log_sensor_id(0)                
            # code_desc = self._get_log_code_desc(unit_id, code)
            # self.data[last_log_id] = f'{ts.strftime("%m/%d/%Y, %H:%M:%S")} {code} {code_desc}'
            return True
        
        return False

    async def update_all_bms_status_data(self):
        if self.busy:
            _LOGGER.debug(f"update_bms_status_data already busy", exc_info=True) 
            return
        self.busy = True 
        for bms_id in range(1, self._bms_qty + 1):
            try:
                result = await self.update_bms_status_data(bms_id)
            except Exception as e:
                self.busy = False 
                _LOGGER.error(f"Error reading bms status data {bms_id}", exc_info=True)
                return

        self.busy = False 
   
        return True   

    async def update_all_log_data(self):
        if self.busy:
            _LOGGER.debug(f"update_all_log_data already busy", exc_info=True) 
            return
        self.busy = True 

        result = False
        self._new_logs = {}
        if len(self.log) == 0:
            log_depth = 7
        else:
            log_depth = 1
        try:
            for unit_id in range(self._bms_qty + 1):
                if unit_id > 0:
                    await asyncio.sleep(.2)
                result = await self.update_log_data(unit_id, log_depth=log_depth)
        except Exception as e:
            _LOGGER.error(f"Error reading log data {unit_id}", exc_info=True)

        if result:
            self.data[f'bmu_logs'] = self.get_log_list(20)
            self._update_balancing_cells_totals()

        self.busy = False 
   
        return True   

    def _update_balancing_cells_totals(self):
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
        
    def _get_balancings_totals_per_module(self, t):
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

    def _get_inverter_model(self,model,id):
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
    
    async def update_info_data(self):
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
        if bmuSerial.startswith('P02') or bmuSerial.startswith('P011'):
            # Modules in Paralel
            bat_type = 'LV'

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

        self.data['application'] = APPLICATION_LIST[application_id]
        self.data['lvs_type'] = lvs_type_id
        self.data['phase'] = PHASE_LIST[phase_id]

        return True

    async def update_ext_info_data(self):
        """start reading info data"""
        regs = await self.get_registers(address=0x0010, count=2)
        if regs is None:
            return False

        inverter_id = self.convert_from_registers_int8(regs[0:1])[0]
        hv_type_id = self.convert_from_registers_int8(regs[1:2])[0]

        model = "NA"
        capacity_module = 0.0
        cells = 0
        sensors_t = 0

        if hv_type_id == 0:
          # HVL -> Lithium Iron Phosphate (LFP), 3-8 Module (12kWh-32kWh), unknown specification, so 0 cells and 0 temps
          model = "HVL"
          capacity_module = 4.0
        elif hv_type_id == 1:
          # HVM 16 Cells per module
          model = "HVM"
          capacity_module = 2.76
          cells = 16
          sensors_t = 8
        elif hv_type_id == 2:
          # HVS 32 cells per module
          model = "HVS"
          capacity_module = 2.56
          cells = 32
          sensors_t = 12
        else:
          if self.data['bat_type'] == 'LV':
            model = "LVS"
            capacity_module = 4.0
            cells = 7

        self._cells = cells
        self._temps = sensors_t
 
        capacity = self._bms_qty * self._modules * capacity_module

        self.data['inverter'] = self._get_inverter_model(model, inverter_id)
        self.data['model'] = model
        self.data['capacity'] = capacity
        self.data['sensors_t'] = sensors_t
        self.data['cells'] = cells

        return True

    async def update_bmu_status_data(self):
        """start reading bmu status data"""
        if self.busy:
            _LOGGER.error(f"read_all_bms_status_data already busy", exc_info=True) 
            return
        self.busy = True 
        regs = await self.get_registers(address=0x0500, count=21) # 1280
        if regs is None:
            self.busy = False 
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
        _LOGGER.debug(f'bmu status reg 9-12: {regs[9:13]}')
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

        self.busy = False 

        return True
       
    async def update_bms_status_data(self, bms_id):
        #_LOGGER.debug(f"update_bms_status_data {bms_id}")
        """start reading status data"""

        await self._client.write_registers(0x0550, [bms_id,0x8100], slave=self._unit_id)
        timeout = 5
        i = 0
        response_reg = 0
        while response_reg != 0x8801 and i < timeout: # wait for the response
            await asyncio.sleep(.2)
            i += 0.2
            try:
                data = await self.read_holding_registers(unit_id=self._unit_id, address=0x0550, count=1)
            except Exception as e:
                _LOGGER.error(f"read bms status error while waiting for response.", exc_info=True)
            if not data.isError():
                response_reg = data.registers[0]
        if response_reg == 0:
            _LOGGER.error(f"read bms status error timeout.", exc_info=True)
            return False

        regs = []
        for i in range(0,4):
            await asyncio.sleep(.05)
            new_regs = await self.get_registers(address=0x0558, count=65)
            if new_regs is None:
                _LOGGER.error(f"failed reading bms status part: {i}", exc_info=True)
                return False
            else:
                regs += new_regs

        if not len(regs) == 260:
            _LOGGER.error(f"unexpected number of bms status regs: {len(regs)}")
            return False

        # skip 1st register with length
        max_voltage = round(self._client.convert_from_registers(regs[1:2], data_type = self._client.DATATYPE.INT16) * 0.001,3)
        if max_voltage > 5:
            _LOGGER.error(f"bms {bms_id} unexpected max voltage {max_voltage}", exc_info=True)
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
        _LOGGER.debug(f'bms {bms_id} reg 20: {regs[20]}')
        bat_voltage = round(self._client.convert_from_registers(regs[21:22], data_type = self._client.DATATYPE.INT16) * 0.1,2)
        # 22 ?
        _LOGGER.debug(f'bms {bms_id} reg 22: {regs[22]}')
        # 23 ? Switch State ?
        _LOGGER.debug(f'bms {bms_id} reg 23: {regs[23]}')
        output_voltage = round(self._client.convert_from_registers(regs[24:25], data_type = self._client.DATATYPE.INT16) * 0.1,2)
        soc = round(self._client.convert_from_registers(regs[25:26], data_type = self._client.DATATYPE.INT16) * 0.1,2)
        soh = self._client.convert_from_registers(regs[26:27], data_type = self._client.DATATYPE.INT16)
        current = round(self._client.convert_from_registers(regs[27:28], data_type = self._client.DATATYPE.INT16) * 0.1,2)
        warnings1 = self._client.convert_from_registers(regs[28:29], data_type = self._client.DATATYPE.UINT16)
        warnings2 = self._client.convert_from_registers(regs[29:30], data_type = self._client.DATATYPE.UINT16)
        warnings3 = self._client.convert_from_registers(regs[30:31], data_type = self._client.DATATYPE.UINT16)
        # 31-47 ?
        _LOGGER.debug(f'bms {bms_id} reg 31-47: {regs[31:48]}')
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

        efficiency = round((discharge_lfte / charge_lfte) * 100.0,1)

        avg_cell_voltage = round(sum(all_cell_voltages) / len(all_cell_voltages),2)
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
    
    async def update_log_data(self, unit_id, log_depth = 1):
        prev = len(self._new_logs)
        for i in range(log_depth):
            await self._read_log_data_unit(unit_id)
            if (len(self._new_logs) - prev) < 20:
                #_LOGGER.debug(f'no new logs found {unit_id} {i} {log_depth} {len(self._new_logs)}')
                break
            prev = len(self._new_logs)
        return True
   
    async def _read_log_data_unit(self, unit_id):
        """start reading log data"""
        await self._client.write_registers(0x05a0, [unit_id,0x8100], slave=self._unit_id)
        timeout = 5
        i = 0
        response_reg = 0
        while response_reg != 0x4000 and i < timeout: # wait for the response
            await asyncio.sleep(.2)
            i += 0.2
            try:
                data = await self.read_holding_registers(unit_id=self._unit_id, address=0x05A1, count=1)
            except Exception as e:
                _LOGGER.error(f"read {self._get_unit_name(unit_id)} log data error while waiting for response.", exc_info=True)
            if not data.isError():
                response_reg = data.registers[0]
        if response_reg == 0:
            _LOGGER.error(f"read log data error timeout.", exc_info=True)
            return False

        regs = []
        for i in range(5):
            await asyncio.sleep(.05)
            new_regs = await self.get_registers(address=0x05A8, count=65)
            if new_regs is None:
                _LOGGER.error(f"failed reading {self._get_unit_name(unit_id)} log part: {i}", exc_info=True)
                return
            else:
                regs += new_regs[1:] # skip first byte 

        if len(regs) == 0 or not len(regs) == 320:
            _LOGGER.error(f"unexpected number of {self._get_unit_name(unit_id)}  log regs: {len(regs)}")
            return False    

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
            ts:datetime = None
            try:
                year += 2000                 
                ts:datetime = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
            except Exception as e:
                _LOGGER.error(f'Failed to derive log timestamp {e}')
                return

            k = f'{ts.strftime("%Y%m%d %H:%M:%S")}-{unit_id}-{code}' 

            if not k in self.log.keys():
                hexdata = binascii.hexlify(data).decode('ascii')
                log = {'ts': ts.timestamp(), 'u': unit_id, 'c': code, 'data': hexdata}
                self._new_logs[k] = log
                self.log[k] = log
                #_LOGGER.debug(f'New log {k} {len(self.log)}')

            if i==0:
                last_log_id = self._get_unit_log_sensor_id(unit_id)                
                code_desc = self._get_log_code_desc(unit_id, code)
                self.data[last_log_id] = f'{ts.strftime("%m/%d/%Y, %H:%M:%S")} {code} {code_desc}'

        self.data['log_count'] = len(self.log)        

        return True

    def _get_unit_log_sensor_id(self, unit_id):    
        if unit_id == 0:
            last_log_id = 'bmu_last_log'      
        else:
            last_log_id = f'bms{unit_id}_last_log' 
        return last_log_id    

    def _get_unit_name(self, unit_id):    
        if unit_id == 0:
            unit = 'BMU'
        else:
            unit = f'BMS {unit_id}'
        return unit    

    def _get_log_code_desc(self, unit_id, code):
        if unit_id == 0:
            code_desc = self.get_value_from_dict(BMU_LOG_CODES, code, 'Not available')
        else:
            code_desc = self.get_value_from_dict(BMS_LOG_CODES, code, 'Not available')
        return code_desc

    def save_log_entries(self, append=True):
        # if append:
        #     self.save_log_txt_file(self._new_logs, append=True)
        # else:
        #     self.save_log_txt_file(self.log)
        self.save_log_csv_file(self.log)
        self.save_log_json_file(self.log)

        _LOGGER.debug(f'Saved {len(self._new_logs)} new log entries. Total: {len(self.log)}')
        return True

    def save_log_json_file(self, logs):
        logs = dict(sorted(logs.items()))
        with open(self._log_json_path, "w") as outfile:
            json.dump(logs, outfile, indent=1, sort_keys=True, default=str)

    def save_log_txt_file(self, logs, append=True):
        logs = dict(sorted(logs.items()))
        if append:
            write_type = 'a'
        else:
            write_type = 'w'
        with open(self._log_txt_path, write_type) as myfile:
            for k, log in logs.items():
                unit_id, unit_name, ts, code, data  = self.split_log_entry(log)
                code_desc, decoded = self.decode_log_data(unit_id, ts, code, data)
                detail = decoded['desc']
                line = f'{ts.strftime("%Y%m%d %H:%M:%S")} {unit_name} {code} {code_desc} {detail}\n' 
                myfile.write(line)

    def save_log_csv_file(self, logs):
        logs = dict(sorted(logs.items()))

        with open(self._log_csv_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['ts', 'unit','code','description','detail','data'])
            
            for k, log in logs.items():
                unit_id, unit_name, ts, code, data  = self.split_log_entry(log)
                code_desc, decoded = self.decode_log_data(unit_id, ts, code, data)
                detail = decoded['desc']
                log_list = [ts.strftime("%Y%m%d %H:%M:%S"), unit_name, code, code_desc, detail, binascii.hexlify(data).decode('ascii')]
                writer.writerow(log_list)

    def split_log_entry(self, log):
        unit_id = int(log['u'])
        unit_name = self._get_unit_name(unit_id)
        code = int(log['c'])
        ts = datetime.fromtimestamp(log['ts'])
        data = bytearray.fromhex(log['data'])

        return unit_id, unit_name, ts, code, data 

    def get_log_list(self, max_length):
        logs = sorted(self.log.items(), reverse=True)
        i = 0
        log_list = []
        for k, log in logs:
            unit_id, unit_name, ts, code, data = self.split_log_entry(log)
            code_desc, decoded = self.decode_log_data(unit_id, ts, code, data)
            detail = decoded.get('desc')
            hexdata = log['data']
            decoded.pop('desc')
            i += 1
            if i>max_length:
                break
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

    def decode_bmu_log_data(self, ts:datetime, code:int, data:bytearray):
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
                datapoints['pt_u'] = ''
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

    def decode_bms_log_data(self, ts:datetime, code:int, data:bytearray):
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
        elif code in [2,3,4,5,6,7,9,10,13,14,16,19,20,21]:            
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
            datapoints['threshold']  = f"{x:d}" + "." + f"{y:d}"
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

    def log_data_to_str(self, data):
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


