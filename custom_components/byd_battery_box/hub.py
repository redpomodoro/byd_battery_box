"""BYD Battery Box Hub."""
from __future__ import annotations

import requests
import threading
import logging
import operator
import threading
from datetime import timedelta
from typing import Optional

from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.core import HomeAssistant

from pymodbus.client import ModbusTcpClient

from .const import (
    DOMAIN,
    INVERTER_LIST,
    APPLICATION_LIST,
    PHASE_LIST,
    ATTR_MANUFACTURER,
    WORKING_AREA
)

_LOGGER = logging.getLogger(__name__)

class Hub:
    """Hub for BYD Battery Box Interface"""

    manufacturer = "BYD"

    def __init__(self, hass: HomeAssistant, name: str, host: str, port: int, unit_id: int, scan_interval: int) -> None:
        """Init hub."""
        self._host = host
        self._port = port
        self._hass = hass
        self._name = name
        self._unit_id = unit_id
        self._lock = threading.Lock()
        self._id = f'{name.lower()}_{host.lower().replace('.','')}'
        self.online = True     
        #_LOGGER.error(f"pymodbus {version('pymodbus')}")          
        self._client = ModbusTcpClient(host=host, port=port, framer='rtu', timeout=max(3, (scan_interval - 1))) 
        self._scan_interval = timedelta(seconds=scan_interval)
        self._unsub_interval_method = None
        self._entities = []
        self.data = {}
        self.data['unit_id'] = unit_id

    #async def init_data(self):
    #    return await self._hass.async_add_executor_job(self._init_data)

    async def init_data(self):
        # try: 
        #     result = self.read_info_data()
        # except Exception as e:
        #     _LOGGER.error(f"Error reading info {self._host}:{self._port} unit id: {self._unit_id} {e}")
        #     raise Exception(f"Error reading inverter info unit id: {self._unit_id}")
        
        result = False
        try: 
            retries = 0
            while result==False and retries<4:
                result = self.read_info_data()
                retries += 1
        except Exception as e:
            _LOGGER.error(f"Error reading info {self._host}:{self._port} unit id: {self._unit_id}", exc_info=True)
            raise Exception(f"Error reading inverter info unit id: {self._unit_id}")

        if result == False:
            _LOGGER.error(f"Error reading info {self._host}:{self._port} unit id: {self._unit_id}")
            #raise Exception(f"Error reading inverter info unit id: {self._unit_id}")

        try:
            result = self.read_ext_info_data()
        except Exception as e:
            _LOGGER.error(f"Error reading ext info data", exc_info=True)

        try:
            result = self.read_status_data()
        except Exception as e:
            _LOGGER.error(f"Error reading status data", exc_info=True)

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
            "serial_number": self.data.get('serial'),
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
        result : bool = await self._hass.async_add_executor_job(self._refresh_modbus_data)
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
            return False

        try:
            update_result = self.read_info_data()
        except Exception as e:
            _LOGGER.exception("Error reading info data", exc_info=True)
            update_result = False

        try:
            update_result = self.read_ext_info_data()
        except Exception as e:
            _LOGGER.error(f"Error reading ext info data", exc_info=True)
            update_result = False

        try:
            update_result = self.read_status_data()
        except Exception as e:
            _LOGGER.exception("Error reading status data", exc_info=True)
            update_result = False

        return update_result

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
        _LOGGER.info(f"read registers a: {address} s: {unit_id} c {count}")
        with self._lock:
            return self._client.read_holding_registers(
                address=address, count=count, slave=unit_id
            )

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

    def read_info_data(self):
        """start reading info data"""
        data = self.read_holding_registers(
            unit_id=self._unit_id, address=0x0000, count=20
        )
        if data.isError():
            _LOGGER.error(f"info data modbus error. {self._host}:{self._port} unit_id {self._unit_id} data:{data}")
            return False

        regs = data.registers

        bmuSerial = self._client.convert_from_registers(regs[0:10], data_type = self._client.DATATYPE.STRING)[:-1]
        self.data['serial'] = bmuSerial
        #self.data['serial'] = "xxxxxxxxxxxxxxxxxxx"  # for screenshots

        if bmuSerial.startswith('P03') or bmuSerial.startswith('E0P3'):
            # Modules in Serial
            bat_type = 'HV'
        if bmuSerial.startswith('P02') or bmuSerial.startswith('P011'):
            # Modules in Paralel
            bat_type = 'LV'

        bmu_v_A_1 = regs[0x000C] >> 8
        bmu_v_A_2 = regs[0x000C] & 0xFF
        bmu_v_A = f'v{bmu_v_A_1}.{bmu_v_A_2}'
        bmu_v_B_1 = regs[0x000D] >> 8
        bmu_v_B_2 = regs[0x000D] & 0xFF
        bmu_v_B = f'v{bmu_v_B_1}.{bmu_v_B_2}'
        bms_v1 = regs[0x000E] >> 8
        bms_v2 = regs[0x000E] & 0xFF
        bms_v = f'v{bms_v1}.{bms_v2}'   

        bmu_area = regs[0x000F] >> 8
        bms_area = regs[0x000F] & 0xFF

        if bmu_area == 0:
            bmu_v = bmu_v_A
        else:
            bmu_v = bmu_v_B

        #inverter_id = (regs[0x0010] >> 8) & 0x0F
        towers = (regs[0x0010] >> 4) & 0x0F
        modules = regs[0x0010] & 0x0F

        application_id = (regs[0x0011] >> 8) & 0xFF
        lvs_type_id = regs[0x0011] & 0xFF
        phase_id = (regs[0x0012] >> 8) & 0xFF
         
        self.data['bat_type'] = bat_type
        self.data['bmu_v_A'] = bmu_v_A
        self.data['bmu_v_B'] = bmu_v_B
        self.data['bmu_v'] = bmu_v
        self.data['bms_v'] = bms_v
        self.data['bmu_area'] = WORKING_AREA[bmu_area]
        self.data['bms_area'] = WORKING_AREA[bms_area]
        self.data['towers'] = towers       
        self.data['modules'] = modules       

        self.data['application'] = APPLICATION_LIST[application_id]
        self.data['lvs_type'] = lvs_type_id
        self.data['phase'] = PHASE_LIST[phase_id]

        return True

    def read_ext_info_data(self):
        """start reading info data"""
        data = self.read_holding_registers(
            unit_id=self._unit_id, address=0x0010, count=2
        )
        if data.isError():
            _LOGGER.error(f"ext info data modbus error. {self._host}:{self._port} unit_id {self._unit_id} data:{data}")
            return False

        regs = data.registers

        inverter_id = regs[0x0000] >> 8
        hv_type_id = regs[0x0001] >> 8

        modules = self.data['modules']
        bms_qty = self.data['towers']

        model = "NA"
        capacity_module = 0.0
        volt_n = 0
        temp_n = 0
        cells_n = 0
        temps_n = 0

        if hv_type_id == 0:
          # HVL -> Lithium Iron Phosphate (LFP), 3-8 Module (12kWh-32kWh), unknown specification, so 0 cells and 0 temps
          model = "HVL"
          capacity_module = 4.0
        elif hv_type_id == 1:
          # HVM 16 Cells per module
          model = "HVM"
          capacity_module = 2.76
          volt_n = 16
          temp_n = 8
          cells_n = modules * volt_n
          temps_n = modules * temp_n
        elif hv_type_id == 2:
          # HVS 32 cells per module
          model = "HVS"
          capacity_module = 2.56
          volt_n = 32
          temp_n = 12
          cells_n = modules * volt_n
          temps_n = modules * temp_n
        else:
          if self.data['bat_type'] == 'LV':
            model = "LVS"
            capacity_module = 4.0
            volt_n = 7
            cells_n = modules * volt_n
 
        capacity = bms_qty * modules * capacity_module

        self.data['inverter'] = self.get_inverter_model(model, inverter_id)
        self.data['model'] = model
        self.data['capacity'] = capacity

       
    def read_status_data(self):
        """start reading status data"""
        data = self.read_holding_registers(
            unit_id=self._unit_id, address=0x0500, count=21
        )
        if data.isError():
            _LOGGER.error(f"status data modbus error. data:{data}")
            return False

        regs = data.registers

        soc = self._client.convert_from_registers(regs[0:1], data_type = self._client.DATATYPE.UINT16)
        max_cell_voltage = round(self._client.convert_from_registers(regs[1:2], data_type = self._client.DATATYPE.UINT16) * 0.01,2)
        min_cell_voltage = round(self._client.convert_from_registers(regs[2:3], data_type = self._client.DATATYPE.UINT16) * 0.01,2)
        soh = self._client.convert_from_registers(regs[3:4], data_type = self._client.DATATYPE.UINT16)
        current = round(self._client.convert_from_registers(regs[4:5], data_type = self._client.DATATYPE.INT16) * 0.1,1)
        bat_voltage = round(self._client.convert_from_registers(regs[5:6], data_type = self._client.DATATYPE.UINT16) * 0.01,2)
        max_cell_temp = self._client.convert_from_registers(regs[6:7], data_type = self._client.DATATYPE.INT16)
        min_cell_temp = self._client.convert_from_registers(regs[7:8], data_type = self._client.DATATYPE.INT16)
        bmu_temp = self._client.convert_from_registers(regs[8:9], data_type = self._client.DATATYPE.INT16)
        error = self._client.convert_from_registers(regs[13:14], data_type = self._client.DATATYPE.UINT16)
        output_voltage = round(self._client.convert_from_registers(regs[16:17], data_type = self._client.DATATYPE.UINT16) * 0.01,2)
        charge_lfte = self._client.convert_from_registers(regs[17:19], data_type = self._client.DATATYPE.UINT32) * 0.001
        discharge_lfte = self._client.convert_from_registers(regs[19:21], data_type = self._client.DATATYPE.UINT32) * 0.001
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
        self.data['error'] = error
        self.data['output_voltage'] = output_voltage
        self.data['power'] = current * output_voltage
        self.data['charge_lfte'] = charge_lfte
        self.data['discharge_lfte'] = discharge_lfte
        self.data['efficiency'] = efficiency

        return True
