#import os, sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))

"""Extended Modbus Class"""

import threading
import logging
import operator
import threading
from typing import Optional, Literal
import struct
import asyncio

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.utilities import unpack_bitstring
from pymodbus.exceptions import ModbusIOException

_LOGGER = logging.getLogger(__name__)

class ExtModbusClient:

    def __init__(self, host: str, port: int, unit_id: int, timeout: int, framer:str) -> None:
        """Init Class"""
        self._lock = threading.Lock()
        self._host = host
        self._port = port
        self._unit_id = unit_id
        self.busy = False
        self._client = AsyncModbusTcpClient(host=host, port=port, framer=framer, timeout=timeout) 

        #_LOGGER.debug(f"pymodbus {version('pymodbus')}")      # Python 3.8
        #_LOGGER.debug(f"pymodbus {pkg_resources.get_distribution("simplegist").version}")
        #_LOGGER.debug(f'python: {platform.python_version()}')

    def close(self):
        """Disconnect client."""
        with self._lock:
            self._client.close()

    async def connect(self):
        """Connect client."""
        result = False
        with self._lock:
            result = await self._client.connect()

        if result:
            _LOGGER.info("successfully connected to %s:%s",
                            self._client.comm_params.host, self._client.comm_params.port)
        else:
            _LOGGER.warning("not able to connect to %s:%s",
                            self._client.comm_params.host, self._client.comm_params.port)
        return result

    @property
    def connected(self) -> bool:
        return self._client.connected

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

    async def read_holding_registers(self, unit_id, address, count):
        """Read holding registers."""
        _LOGGER.debug(f"read registers a: {address} s: {unit_id} c {count} {self._client.connected}")
        with self._lock:
            return await self._client.read_holding_registers(
                address=address, count=count, slave=unit_id
            )

    async def get_registers(self, address, count, retries = 0):
        data = await self.read_holding_registers( unit_id=self._unit_id, address=address, count=count)
        if data.isError():
            if isinstance(data,ModbusIOException):
                if retries < 1:
                    _LOGGER.debug(f"IO Error: {data}. Retrying...")
                    return await self.get_registers(address=address, count=count, retries = retries + 1)
                else:
                    _LOGGER.error(f"error reading register: {address} count: {count} unit id: {self._unit_id} error: {data} ")
            else:
                _LOGGER.error(f"error reading register: {address} count: {count} unit id: {self._unit_id} error: {data} ")
            return None
        return data.registers

    async def write_registers(self, unit_id, address, payload):
        """Write registers."""
        _LOGGER.info(f"write registers a: {address} p: {payload}")
        with self._lock:
            return await self._client.write_registers(
                address=address, values=payload, slave=unit_id
            )

    def calculate_value(self, value, sf, digits=2):
        return round(value * 10**sf, digits)

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
        cls, registers: list[int], data_type: AsyncModbusTcpClient.DATATYPE, word_order: Literal["big", "little"] = "big"
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

    def get_value_from_dict(self, d, k, default='NA'):
        v = d.get(k)
        if not v is None:
            return v
        return f'{default}'
    
    def convert_from_byte_uint16(self, byteArray, pos, type='BE'): 
        try:
            if type == 'BE':
                result = byteArray[pos] * 256 + byteArray[pos + 1]
            else:
                result = byteArray[pos+1] * 256 + byteArray[pos]
        except:
          return 0
        return result

    def convert_from_byte_int16(self, byteArray, pos, type='BE'): 
        try:
            if type == 'BE':
                result = byteArray[pos] * 256 + byteArray[pos + 1]
            else:
                result = byteArray[pos+1] * 256 + byteArray[pos]
            if (result > 32768):
                result -= 65536
        except:
          return 0
        return result

    def bitmask_to_strings(self, bitmask, bitmask_list, bits=16):
        strings = []
        len_list = len(bitmask_list)
        for bit in range(bits):
            if bitmask & (1<<bit):
                if bit < len_list: 
                    value = bitmask_list[bit]
                else:
                    value = f'bit {bit} undefined'
                strings.append(value)
        return strings

    def bitmask_to_string(self, bitmask, bitmask_list, default='NA', max_length=255, bits=16):
        strings = self.bitmask_to_strings(bitmask = bitmask, bitmask_list = bitmask_list, bits = bits)
        return self.strings_to_string(strings=strings, default=default, max_length=max_length)
    
    def strings_to_string(self, strings, default='NA', max_length=255):
        if len(strings):
            return ','.join(strings)[:max_length]
        return default
