"""BYD Battery Box Hub."""
from __future__ import annotations

import threading
import logging
import operator
import threading
from datetime import timedelta, datetime
from typing import Optional, Literal
import struct
import asyncio
#from typing import Generic, Literal, TypeVar, cast
#from importlib.metadata import version
#import pkg_resources
#import platform

from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.core import HomeAssistant

from pymodbus.client import ModbusTcpClient
from pymodbus.utilities import unpack_bitstring
from pymodbus.exceptions import ModbusIOException

from .const import (
    DOMAIN,
    INVERTER_LIST,
    APPLICATION_LIST,
    PHASE_LIST,
    ATTR_MANUFACTURER,
    WORKING_AREA,
    BMU_ERRORS,
    BMS_WARNINGS,
    BMS_WARNINGS3,
    BMS_ERRORS
)

_LOGGER = logging.getLogger(__name__)

class Hub:
    """Hub for BYD Battery Box Interface"""

    manufacturer = "BYD"

    def __init__(self, hass: HomeAssistant, name: str, host: str, port: int, unit_id: int, scan_interval: int, scan_interval_bms: int = 600) -> None:
        """Init hub."""
        self._host = host
        self._port = port
        self._hass = hass
        self._name = name
        self._unit_id = unit_id
        self._lock = threading.Lock()
        self._id = f'{name.lower()}_{host.lower().replace('.','')}'
        self.online = True     
        #_LOGGER.debug(f"pymodbus {version('pymodbus')}")      # Python 3.8
        #_LOGGER.debug(f"pymodbus {pkg_resources.get_distribution("simplegist").version}")
        #_LOGGER.debug(f'python: {platform.python_version()}')

        self._initialized = False
        self._last_update_bms = None
        self._unsub_interval_method = None
        self._entities = []
        self._bms_qty = 0
        self._modules = 0
        self._cells = 0 # number of cells per module
        self._temps = 0 # number of temp sensors per module
        self.data = {}
        self.data['unit_id'] = unit_id
        self._scan_interval = timedelta(seconds=scan_interval)
        self._scan_interval_bms = timedelta(seconds=scan_interval_bms)
        self._client = ModbusTcpClient(host=host, port=port, framer='rtu', timeout=max(3, (scan_interval - 1))) 

    async def init_data(self, close = False, read_status_data = False):
        result = False

        self.connect()
        try: 
            retries = 0
            result = self.read_info_data()
            while result==False and retries<4:
                await asyncio.sleep(.1)
                result = self.read_info_data()
                retries += 1
        except Exception as e:
            _LOGGER.error(f"Error reading base info {self._host}:{self._port} unit id: {self._unit_id}", exc_info=True)
            raise Exception(f"Error reading base info unit id: {self._unit_id}")

        if result == False:
            _LOGGER.error(f"Error reading info {self._host}:{self._port} unit id: {self._unit_id}")

        try:
            result = self.read_ext_info_data()
        except Exception as e:
            _LOGGER.error(f"Error reading ext info data", exc_info=True)
            raise Exception(f"Error reading ext info unit id: {self._unit_id}")

        if read_status_data:
            try:
                result = self.read_bmu_status_data()
            except Exception as e:
                _LOGGER.error(f"Error reading status data", exc_info=True)

            for bms_id in range(1, self._bms_qty + 1):
                try:
                    result = await self.read_bms_status_data(bms_id)
                except Exception as e:
                    _LOGGER.error(f"Error reading bms status data", exc_info=True)

        if close:
            self.close()
        self._initialized = True

        _LOGGER.debug(f"init done. data: {self.data}")          

        return True

    @property 
    def device_info_bmu(self) -> dict:
        return {
            "identifiers": {(DOMAIN, f'{self._name}_byd_bmu')},
            "name": f'Battery Management Unit',
            "manufacturer": ATTR_MANUFACTURER,
            "model": self.data.get('model'),
            "serial_number": self.data.get('serial'),
            "sw_version": self.data.get('bmu_v'),
        }

    def get_device_info_bms(self,id) -> dict:
        return {
            "identifiers": {(DOMAIN, f'{self._name}_byd_bms_{id}')},
            "name": f'Battery Management System {id}',
            "manufacturer": ATTR_MANUFACTURER,
            "model": self.data.get('model'),
            #"serial_number": self.data.get('serial'),
            "sw_version": self.data.get('bms_v'),
        }
    
    @property
    def hub_id(self) -> str:
        """ID for hub."""
        return self._id

    @callback
    def async_add_hub_entity(self, update_callback):
        """Listen for data updates."""
        # This is the first entity, set up interval.
        if not self._entities:
            # self.connect()
            self._unsub_interval_method = async_track_time_interval(
                self._hass, self.async_refresh_modbus_data, self._scan_interval
            )

        self._entities.append(update_callback)

    @callback
    def async_remove_hub_entity(self, update_callback):
        """Remove data update."""
        self._entities.remove(update_callback)

        if not self._entities:
            """stop the interval timer upon removal of last entity"""
            self._unsub_interval_method()
            self._unsub_interval_method = None
            self.close()

    async def async_refresh_modbus_data(self, _now: Optional[int] = None) -> dict:
        """Time to update."""
        # Skip if init isn't done yet
        if self._initialized == False:
            return
        
        result : bool = await self._hass.async_add_executor_job(self._refresh_modbus_data)

        if result == False:
            return 
        for update_callback in self._entities:
            update_callback()

        if self._last_update_bms is None or ((datetime.now()-self._last_update_bms) > self._scan_interval_bms):
            for bms_id in range(1, self._bms_qty + 1):
                try:
                    result = await self.read_bms_status_data(bms_id)
                except Exception as e:
                    _LOGGER.exception("Error reading bms status data", exc_info=True)
                    result = False           

        if result:
            for update_callback in self._entities:
                update_callback()

    def validate(self, value, comparison, against):
        ops = {
            ">": operator.gt,
            "<": operator.lt,
            ">=": operator.ge,
            "<=": operator.le,
            "==": operator.eq,
            "!=": operator.ne,
        }
        if not ops[comparison](value, against):
            raise ValueError(f"Value {value} failed validation ({comparison}{against})")
        return value

    def _refresh_modbus_data(self, _now: Optional[int] = None) -> bool:
        """Time to update."""
        if not self._entities:
            return False

        if not self._check_and_reconnect():
            #if not connected, skip
            if not self._client.connected:
                _LOGGER.debug("Client not conenected skip update")
                return False

        try:
            result = self.read_bmu_status_data()
        except Exception as e:
            _LOGGER.exception("Error reading status data", exc_info=True)
            result = False

        return result

    async def test_connection(self) -> bool:
        """Test connectivity"""
        try:
            return self.connect()
        except Exception as e:
            _LOGGER.exception("Error connecting to the device", exc_info=True)
            return False

    def close(self):
        """Disconnect client."""
        with self._lock:
            self._client.close()

    def _check_and_reconnect(self):
        if not self._client.connected:
            _LOGGER.info("modbus client is not connected, trying to reconnect")
            return self.connect()

        return self._client.connected

    def connect(self):
        """Connect client."""
        result = False
        with self._lock:
            result = self._client.connect()

        if result:
            _LOGGER.info("successfully connected to %s:%s",
                            self._client.comm_params.host, self._client.comm_params.port)
        else:
            _LOGGER.warning("not able to connect to %s:%s",
                            self._client.comm_params.host, self._client.comm_params.port)
        return result

    def read_holding_registers(self, unit_id, address, count):
        """Read holding registers."""
        _LOGGER.debug(f"read registers a: {address} s: {unit_id} c {count} {self._client.connected}")
        with self._lock:
            return self._client.read_holding_registers(
                address=address, count=count, slave=unit_id
            )

    def get_registers(self, address, count, retries = 0):
        data = self.read_holding_registers( unit_id=self._unit_id, address=address, count=count)
        if data.isError():
            if isinstance(data,ModbusIOException):
                if retries < 1:
                    _LOGGER.debug(f"IO Error: {data}. Retrying...")
                    return self.get_registers(address=address, count=count, retries = retries + 1)
                else:
                    _LOGGER.error(f"error reading register: {address} count: {count} unit id: {self._unit_id} error: {data} ")
            else:
                _LOGGER.error(f"error reading register: {address} count: {count} unit id: {self._unit_id} error: {data} ")
            return None
        return data.registers

    def write_registers(self, unit_id, address, payload):
        """Write registers."""
        _LOGGER.info(f"write registers a: {address} p: {payload}")
        with self._lock:
            return self._client.write_registers(
                address=address, values=payload, slave=unit_id
            )

    def calculate_value(self, value, sf):
        return value * 10**sf

    def strip_escapes(self, value:str):
        if value is None:
            return
        filter = ''.join([chr(i) for i in range(0, 32)])
        return value.translate(str.maketrans('', '', filter)).strip()

    def convert_from_registers_int8(self, regs):
        return [int(regs[0] >> 8), int(regs[0] & 0xFF)]

    def convert_from_registers_int4(self, regs):
        result = [int(regs[0] >> 4) & 0x0F, int(regs[0] & 0x0F)]
        return result

    def convert_from_registers(
        cls, registers: list[int], data_type: ModbusTcpClient.DATATYPE, word_order: Literal["big", "little"] = "big"
    ) -> int | float | str | list[bool] | list[int] | list[float]:
        """Convert registers to int/float/str.

        # TODO: remove this function once HA has been upgraded to later pymodbus version

        :param registers: list of registers received from e.g. read_holding_registers()
        :param data_type: data type to convert to
        :param word_order: "big"/"little" order of words/registers
        :returns: scalar or array of "data_type"
        :raises ModbusException: when size of registers is not a multiple of data_type
        """
        if not (data_len := data_type.value[1]):
            byte_list = bytearray()
            if word_order == "little":
                registers.reverse()
            for x in registers:
                byte_list.extend(int.to_bytes(x, 2, "big"))
            if data_type == cls.DATATYPE.STRING:
                trailing_nulls_begin = len(byte_list)
                while trailing_nulls_begin > 0 and not byte_list[trailing_nulls_begin - 1]:
                    trailing_nulls_begin -= 1
                byte_list = byte_list[:trailing_nulls_begin]
                return byte_list.decode("utf-8")
            return unpack_bitstring(byte_list)
        if (reg_len := len(registers)) % data_len:
            raise Exception(
                f"Registers illegal size ({len(registers)}) expected multiple of {data_len}!"
            )

        result = []
        for i in range(0, reg_len, data_len):
            regs = registers[i:i+data_len]
            if word_order == "little":
                regs.reverse()
            byte_list = bytearray()
            for x in regs:
                byte_list.extend(int.to_bytes(x, 2, "big"))
            result.append(struct.unpack(f">{data_type.value[0]}", byte_list)[0])
        return result if len(result) != 1 else result[0]

    def get_inverter_model(self,model,id):
        # Mapping from Be_Connect (Setup Home) 
        if model == "LVS":                                     # LVS
          if id == 0:
            return INVERTER_LIST[0]                              # Fronius HV
          elif (id == 1) or (id == 2):
            return INVERTER_LIST[1]                              # Goodwe HV/Viessmann HV
          elif id == 3:
            return INVERTER_LIST[2]                              # KOSTAL HV
          elif id == 4:
            return INVERTER_LIST[18]                             # Selectronic LV
          elif id == 5:
            return INVERTER_LIST[3]                              # SMA SBS3.7/5.0/6.0 HV
          elif id == 6:
            return INVERTER_LIST[19]                             # SMA LV
          elif id == 7:
            return INVERTER_LIST[20]                             # Victron LV
          elif id == 8:
            return INVERTER_LIST[30]                             # Suntech LV
          elif id == 9:
            return INVERTER_LIST[4]                              # Sungrow HV
          elif id == 10:
            return INVERTER_LIST[5]                              # KACO_HV
          elif id == 11:
            return INVERTER_LIST[21]                             # Studer LV
          elif id == 12:
            return INVERTER_LIST[28]                             # SolarEdge LV
          elif id == 13:
            return INVERTER_LIST[6]                              # Ingeteam HV
        elif model == "HVL":                                  # HVL
          if id == 0:
            return INVERTER_LIST[1]
          elif id == 1:
            return INVERTER_LIST[3]
          elif id == 2:
            return INVERTER_LIST[8]
          elif id == 3:
            return INVERTER_LIST[10]
          elif id == 4:
            return INVERTER_LIST[17]
        else:                                                    # HVM, HVS
          if (id >= 0) and (id <= 16):
            return INVERTER_LIST[id]
        _LOGGER.error(f"unknown inverter. model: {model} inverter id: {id}")
        return "NA"

    def bitmask_to_string(self, bitmask, bitmask_list, default='NA', max_length=255, bits=16):
        strings = []
        len_list = len(bitmask_list)
        for bit in range(bits):
            if bitmask & (1<<bit):
                if bit < len_list: 
                    value = bitmask_list[bit]
                else:
                    value = f'bit {bit} undefined'
                strings.append(value)

        if len(strings):
            return ','.join(strings)[:max_length]
        return default
    
    def read_info_data(self):
        """start reading info data"""
        regs = self.get_registers(address=0x0000, count=20)
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

    def read_ext_info_data(self):
        """start reading info data"""
        regs = self.get_registers(address=0x0010, count=2)
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

        self.data['inverter'] = self.get_inverter_model(model, inverter_id)
        self.data['model'] = model
        self.data['capacity'] = capacity
        self.data['sensors_t'] = sensors_t
        self.data['cells'] = cells

        return True

    def read_bmu_status_data(self):
        """start reading bmu status data"""
        regs = self.get_registers(address=0x0500, count=21) # 1280
        if regs is None:
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

        return True
       
    async def read_bms_status_data(self, bms_id):
        """start reading status data"""

        self._client.write_registers(0x0550, [bms_id,0x8100], slave=self._unit_id)
        timeout = 5
        i = 0
        response_reg = 0
        while response_reg != 0x8801 and i < timeout: # wait for the response
            await asyncio.sleep(.2)
            i += 0.2
            try:
                data = self.read_holding_registers(unit_id=self._unit_id, address=0x0550, count=1)
            except Exception as e:
                _LOGGER.error(f"read bms status error while waiting for response.", exc_info=True)
            if not data.isError():
                response_reg = data.registers[0]
        if response_reg == 0:
            _LOGGER.error(f"read bms status error timeout.", exc_info=True)
            return False
        await asyncio.sleep(.1)

        regs = []
        for i in range(0,4):
            new_regs = self.get_registers(address=0x0558, count=65)
            if new_regs is None:
                _LOGGER.error(f"failed reading bms status part: {i}", exc_info=True)
            else:
                regs = regs + new_regs

        if not len(regs) == 260:
            _LOGGER.error(f"unexpected number of bmu status regs: {len(regs)}")
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
                b = flags & (1<<bit)
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

        updated = datetime.now()
        self._last_update_bms = updated

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

        self.data[f'bms{bms_id}_warnings'] = self.bitmask_to_string(warnings1, BMS_WARNINGS, 'Normal') + self.bitmask_to_string(warnings2, BMS_WARNINGS, 'Normal') + self.bitmask_to_string(warnings3, BMS_WARNINGS3, 'Normal')
        self.data[f'bms{bms_id}_errors'] = self.bitmask_to_string(errors, BMS_ERRORS, 'Normal')    

        self.data[f'bms{bms_id}_cell_balancing'] = cell_balancing
        self.data[f'bms{bms_id}_cell_voltages'] = cell_voltages
        self.data[f'bms{bms_id}_avg_c_v'] = avg_cell_voltage

        self.data[f'bms{bms_id}_cell_temps'] = cell_temps
        self.data[f'bms{bms_id}_avg_c_t'] = avg_cell_temp

        self.data[f'bms{bms_id}_updated'] = updated

        return True