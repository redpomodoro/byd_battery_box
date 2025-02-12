"""BYD Battery Box Hub."""
from __future__ import annotations

import asyncio
import logging
#import threading
from datetime import timedelta, datetime
from typing import Optional, Literal
from .bydboxclient import BydBoxClient

from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    ATTR_MANUFACTURER,
)

_LOGGER = logging.getLogger(__name__)

class Hub:
    """Hub for BYD Battery Box Interface"""

    manufacturer = "BYD"

    def __init__(self, hass: HomeAssistant, name: str, host: str, port: int, unit_id: int, scan_interval: int, scan_interval_bms: int = 600) -> None:
        """Init hub."""
        self._hass = hass
        self._name = name
        #self._lock = threading.Lock()
        self._id = f'{name.lower()}_{host.lower().replace('.','')}'
        self._last_full_update = None
        self._unsub_interval_method = None
        self._entities = []
        self._scan_interval = timedelta(seconds=scan_interval)
        self._scan_interval_bms = timedelta(seconds=scan_interval_bms)
        self._bydclient = BydBoxClient(host=host, port=port, unit_id=unit_id, timeout=max(3, (scan_interval - 1)))
        self.online = True     
        self._busy = False

    @property 
    def device_info_bmu(self) -> dict:
        return {
            "identifiers": {(DOMAIN, f'{self._name}_byd_bmu')},
            "name": f'Battery Management Unit',
            "manufacturer": ATTR_MANUFACTURER,
            "model": self._bydclient.data.get('model'),
            "serial_number": self._bydclient.data.get('serial'),
            "sw_version": self._bydclient.data.get('bmu_v'),
        }

    def get_device_info_bms(self,id) -> dict:
        return {
            "identifiers": {(DOMAIN, f'{self._name}_byd_bms_{id}')},
            "name": f'Battery Management System {id}',
            "manufacturer": ATTR_MANUFACTURER,
            "model": self._bydclient.data.get('model'),
            #"serial_number": self._bydclient.data.get('serial'),
            "sw_version": self._bydclient.data.get('bms_v'),
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
            self._unsub_interval_method = async_track_time_interval(
                self._hass, self.async_update_data, self._scan_interval
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

    def toggle_busy(func):
        async def wrapper(self, *args, **kwargs):
            if self._busy:
                #_LOGGER.debug(f"hub already busy {func.__name__}") 
                return
            #_LOGGER.debug(f"Busy hub on {func.__name__}")
            self._busy = True
            result = await func(self, *args, **kwargs)
            self._busy = False
            #_LOGGER.debug(f"Busy hub off {func.__name__}")
            return result
        return wrapper

    @toggle_busy
    async def init_data(self, close = False, read_status_data = False):
        await self._hass.async_add_executor_job(self._bydclient.update_log_from_file)  
        await self._bydclient.init_data(close = close, read_status_data=read_status_data)

    @toggle_busy
    async def async_update_data(self, _now: Optional[int] = None) -> dict:
        """Time to update."""
        # if self._busy:
        #     #_LOGGER.debug('Skipping update client busy')
        #     return

    #     await self.update_data()

    # @toggle_busy
    # async def update_data(self):
        if not self._bydclient.initialized:
            return

        connected = await self._check_and_reconnect()
        if not connected:
            if not self._bydclient.connected:
                _LOGGER.warning("Client not conenected skip update")
                return False

        try:
            result = await self._bydclient.update_bmu_status_data()
        except Exception as e:
            _LOGGER.error("Error reading status data")
            return False
        
        if result == False:
            return 
        self.update_entities()

        if self._last_full_update is None or ((datetime.now()-self._last_full_update) > self._scan_interval_bms):
            result = await self._bydclient.update_all_bms_status_data()
            if result:
                self._last_full_update = datetime.now()
                self.update_entities()

            prev_len_log = len(self._bydclient.log)
            result = await self._bydclient.update_all_log_data()
            if result:
                self.update_entities()
                if prev_len_log != len(self._bydclient.log):
                    result : bool = await self._hass.async_add_executor_job(self._bydclient.save_log_entries)

    def update_entities(self):
        for update_callback in self._entities:
            update_callback()

    async def test_connection(self) -> bool:
        """Test connectivity"""
        try:
            return await self.connect()
        except Exception as e:
            _LOGGER.exception("Error connecting to the device")
            return False

    def close(self):
        """Disconnect client."""
        #with self._lock:
        self._bydclient.close()

    async def _check_and_reconnect(self):
        if not self._bydclient.connected:
            _LOGGER.info("BYD battery box client is not connected, trying to reconnect")
            return await self.connect()

        return self._bydclient.connected

    async def connect(self):
        """Connect client."""
        result = False
        #with self._lock:
        result = await self._bydclient.connect()

        return result

    @property
    def data(self):
        return self._bydclient.data
