"""BYD Battery Box Hub."""
from __future__ import annotations

import threading
import logging
import threading
from datetime import timedelta, datetime
from typing import Optional, Literal
import asyncio
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
        self._lock = threading.Lock()
        self._id = f'{name.lower()}_{host.lower().replace('.','')}'
        self._last_full_update = None
        self._unsub_interval_method = None
        self._entities = []
        self._scan_interval = timedelta(seconds=scan_interval)
        self._scan_interval_bms = timedelta(seconds=scan_interval_bms)
        self._bydclient = BydBoxClient(host=host, port=port, unit_id=unit_id, timeout=max(3, (scan_interval - 1)))
        #self.online = True     
        self._busy = True

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
            # self.connect()
            self._unsub_interval_method = async_track_time_interval(
                self._hass, self.async_refresh_byd_box_data, self._scan_interval
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

    async def init_data(self, close = False, read_status_data = False):
        result = await self._hass.async_add_executor_job(self._bydclient.update_logs_from_file)  
        self._busy = True      
        result = await self._bydclient.init_data(close = close, read_status_data=read_status_data)
        self._busy = False      
        return

    # async def async_refresh_byd_box_data_new(self, _now: Optional[int] = None) -> dict:
    #     _LOGGER.error(f"async_refresh_byd_box_data_new {self._bydclient.initialized}" )
    #     """Time to update."""
    #     # Skip if init isn't done yet
    #     if self._bydclient.initialized == False:
    #         return

    #     """Time to update."""
    #     if not self._entities:
    #         return False

    #     if not self._check_and_reconnect():
    #         if not self._bydclient.connected:
    #             _LOGGER.debug("Client not conenected skip update")
    #             return False

    #     try:
    #         result = self._bydclient.update_bmu_status_data()
    #     except Exception as e:
    #         _LOGGER.exception("Error reading status data", exc_info=True)
    #         result = False

    #     if result == False:
    #         return 
    #     for update_callback in self._entities:
    #         update_callback()

    #     if self._last_full_update is None or ((datetime.now()-self._last_full_update) > self._scan_interval_bms):
    #         await self._bydclient.read_all_bms_status_data()

    #     if result:
    #         for update_callback in self._entities:
    #             update_callback()

    async def async_refresh_byd_box_data(self, _now: Optional[int] = None) -> dict:
        """Time to update."""
        if not self._bydclient.initialized:
            return
        if self._busy:
            #_LOGGER.debug('Skipping update client busy')
            return

        #result : bool = await self._hass.async_add_executor_job(self._refresh_byd_box_data)

        connected = await self._check_and_reconnect()
        if not connected:
            if not self._bydclient.connected:
                _LOGGER.debug("Client not conenected skip update")
                return False

        try:
            result = await self._bydclient.update_bmu_status_data()
        except Exception as e:
            _LOGGER.exception("Error reading status data", exc_info=True)
            return False



        if result == False:
            return 
        for update_callback in self._entities:
            update_callback()

        if self._last_full_update is None or ((datetime.now()-self._last_full_update) > self._scan_interval_bms):
            self._busy = True
            result = await self._bydclient.update_all_bms_status_data()
            if result:
                self._last_full_update = datetime.now()
                for update_callback in self._entities:
                    update_callback()

            prev_len_logs = len(self._bydclient.logs)
            result = await self._bydclient.update_all_log_data()
            if result:
                for update_callback in self._entities:
                    update_callback()
                if prev_len_logs != len(self._bydclient.logs):
                    result : bool = await self._hass.async_add_executor_job(self._bydclient.save_log_entries)
            self._busy = False

    # def _refresh_byd_box_data(self, _now: Optional[int] = None) -> bool:
    #     """Time to update."""
    #     if not self._entities:
    #         return False

    #     if not self._check_and_reconnect():
    #         if not self._bydclient.connected:
    #             _LOGGER.debug("Client not conenected skip update")
    #             return False

    #     try:
    #         result = self._bydclient.update_bmu_status_data()
    #     except Exception as e:
    #         _LOGGER.exception("Error reading status data", exc_info=True)
    #         result = False

    #     return result

    async def test_connection(self) -> bool:
        """Test connectivity"""
        try:
            return await self.connect()
        except Exception as e:
            _LOGGER.exception("Error connecting to the device", exc_info=True)
            return False

    def close(self):
        """Disconnect client."""
        with self._lock:
            self._bydclient.close()

    async def _check_and_reconnect(self):
        if not self._bydclient.connected:
            _LOGGER.info("BYD battery box client is not connected, trying to reconnect")
            return await self.connect()

        return self._bydclient.connected

    def connect(self):
        """Connect client."""
        result = False
        with self._lock:
            result = self._bydclient.connect()

        return result

    @property
    def data(self):
        return self._bydclient.data
