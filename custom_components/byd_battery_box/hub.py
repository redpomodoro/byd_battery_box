"""BYD Battery Box Hub."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta, datetime
from typing import Optional, Literal
from .bydboxclient import BydBoxClient

from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    ATTR_MANUFACTURER,
    DEVICE_TYPES
)

_LOGGER = logging.getLogger(__name__)

class Hub:
    """Hub for BYD Battery Box Interface"""

    def __init__(self, hass: HomeAssistant, name: str, host: str, port: int, unit_id: int, scan_interval: int, scan_interval_bms: int = 600, scan_interval_log: int = 600) -> None:
        """Init hub."""
        self._hass = hass
        self._name = name
        self._id = f'{name.lower()}_{host.lower().replace('.','')}'
        self._last_full_update = datetime(2000,1,1)
        self._last_log_update = datetime(2000,1,1)
        self._last_update = datetime(2000,1,1)
        self._unsub_interval_method = None
        self._entities = []
        self._min_update_interval = timedelta(seconds=1)
        self._scan_interval = timedelta(seconds=scan_interval)
        self._scan_interval_bms = timedelta(seconds=scan_interval_bms)
        self._scan_interval_log = timedelta(seconds=scan_interval_log)
        self._bydclient = BydBoxClient(host=host, port=port, unit_id=unit_id, timeout=max(3, (scan_interval - 1)))
        self.online = True     
        self._busy = False
        self._update_log_history_depth = [0,0]

    @property
    def data(self):
        return self._bydclient.data

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
                #_LOGGER.debug(f"skip {func.__name__} hub busy") 
                return
            self._busy = True
            error = None
            try:
                result = await func(self, *args, **kwargs)
            except Exception as e:
                _LOGGER.warning(f'Exception in wrapper {e}')
                error = e
            self._busy = False
            if not error is None:
                raise error
            return result
        return wrapper

    @toggle_busy
    async def init_data(self, close = False):
        await self._hass.async_add_executor_job(self._bydclient.update_log_from_file)  
        await self._bydclient.init_data(close = close)
        self.update_entities()

    @toggle_busy
    async def async_update_data(self, _now: Optional[int] = None) -> dict:
        """Time to update."""
        if not self._bydclient.initialized:
            return

        if ((datetime.now()-self._last_update) < self._min_update_interval):
            #_LOGGER.debug(f"Skip update give system a break ;-)")
            return

        # update log history
        unit_id = self._update_log_history_depth[0]
        log_depth = self._update_log_history_depth[1]
        if self._update_log_history_depth[1] > 0:
            prev_len_log = len(self._bydclient.log)
            _LOGGER.warning(f"Started loading {DEVICE_TYPES[unit_id]} log history; all other data updates will be suspended!")
            try:
                await self._bydclient.update_log_data(unit_id, log_depth=log_depth)
                self._last_log_update = datetime.now()
                self._last_update = datetime.now()
            except Exception as e:
                _LOGGER.error(f'Failed updating {DEVICE_TYPES[unit_id]} log history {self._update_log_history_depth} {e}', exc_info=True)
                return False
            self._update_log_history_depth[1] = 0
            if prev_len_log != len(self._bydclient.log):
                result : bool = await self._hass.async_add_executor_job(self._bydclient.save_log_entries)
            return True

        # update last log data
        if ((datetime.now()-self._last_log_update) > self._scan_interval_log):
            #_LOGGER.debug(f"start update log data")
            prev_len_log = len(self._bydclient.log)
            result = await self._bydclient.update_all_log_data()
            self._last_log_update = datetime.now()
            self._last_update = datetime.now()
            if result:
                self.update_entities()
                if prev_len_log != len(self._bydclient.log):
                    result : bool = await self._hass.async_add_executor_job(self._bydclient.save_log_entries)
                _LOGGER.debug(f"updated log data")
            else:
                _LOGGER.error(f"update log data failed")
                await asyncio.sleep(5)

        # update bms data
        if ((datetime.now()-self._last_full_update) > self._scan_interval_bms):
            #_LOGGER.debug(f"start update BMS status")
            result = await self._bydclient.update_all_bms_status_data()
            if result:
                self._last_full_update = datetime.now()
                self._last_update = datetime.now()
                self.update_entities()
                _LOGGER.debug(f"updated BMS status")
            else:
                _LOGGER.error(f"update BMS status data failed")
                await asyncio.sleep(5)

        # update bmu
        try:
            #_LOGGER.debug(f"start update BMU status")
            result = await self._bydclient.update_bmu_status_data()
        except Exception as e:
            _LOGGER.error(f"Error reading BMU status data connection {self._bydclient.connected} error: {e} ", exc_info=True)
            return False
        if result:
            self._last_update = datetime.now()
            self.update_entities()
            _LOGGER.debug(f"updated BMU status")
        else:
            _LOGGER.warning(f"update BMU status data failed {self._bydclient.connected}")
            return False

        return True

    def update_entities(self):
        for update_callback in self._entities:
            update_callback()

    def close(self):
        """Disconnect client."""
        self._bydclient.close()
        _LOGGER.debug(f"close hub")
    
    async def test_connection(self) -> bool:
        """Test connectivity"""
        _LOGGER.debug(f"test connection")
        try:
            return await self._bydclient.connect()
        except Exception as e:
            _LOGGER.exception("Error connecting to the device")
            return False

    def start_update_log_history(self, unit_id, log_depth):
         _LOGGER.info(f"Scheduled {DEVICE_TYPES[unit_id]} log update for up to {log_depth*20} log entries.")
         self._update_log_history_depth = [unit_id, log_depth]
