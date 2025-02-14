"""Platform for sensor integration."""
from __future__ import annotations

import logging
from typing import Optional, Dict, Any

from homeassistant.components.button import ButtonEntity
from homeassistant.const import CONF_NAME #, CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import Entity

from . import HubConfigEntry
from .const import (
    BMU_BUTTON_TYPES,
    ENTITY_PREFIX,
)
from .hub import Hub

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: HubConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add sensors for passed config_entry in HA."""
    hub:Hub = config_entry.runtime_data
    #hub_name = config_entry.data[CONF_NAME]

    entities = []

    for info in BMU_BUTTON_TYPES.values():
        button = BydBoxButton(
            platform_name = ENTITY_PREFIX,
            hub = hub,
            device_info = hub.device_info_bmu,
            name = info[0],
            key = info[1],
            device_class = info[2],
#            state_class = info[3],
#            unit = info[4],
            icon = info[5],
            entity_category = info[6],
        )
        entities.append(button)

    towers = hub.data.get('towers')
    if not towers is None and towers > 0:
        for id in range(1,towers +1):
            for info in BMU_BUTTON_TYPES.values():
                sensor = BydBoxButton(
                    platform_name = ENTITY_PREFIX,
                    hub = hub,
                    device_info = hub.get_device_info_bms(id),
                    name = f'BMS {id} ' + info[0],
                    key = f'bms{id}_' + info[1],
                    device_class = info[2],
        #            state_class = info[3],
        #            unit = info[4],
                    icon = info[5],
                    entity_category = info[6],
                )
                entities.append(sensor)

    async_add_entities(entities)
    return True

class BydBoxButton(ButtonEntity):
    """Representation of an BYD Battery Box Modbus sensor."""

    def __init__(self, platform_name, hub, device_info, name, key, device_class, icon, entity_category):
#    def __init__(self, platform_name, hub, device_info, name, key, device_class, state_class, unit, icon, entity_category):
        """Initialize the sensor."""
        self._platform_name = platform_name
        self._hub:Hub = hub
        self._key = key
        self._name = name
#        self._unit_of_measurement = unit
        self._icon = icon
        self._device_info = device_info
        if not device_class is None:
            self._attr_device_class = device_class
#        if not state_class is None:
#            self._attr_state_class = state_class
        self._attr_entity_category = entity_category

    async def async_local_poll(self) -> None:
        """Async: Poll the latest data and states from the entity."""
        #no state required for ButtonEntity
        pass

    async def async_press(self) -> None:
        """Async: Handle button press"""

        parts = self._key.split('_')
        log_depth = int(float(parts[-1]) * 0.05)
        device = parts[0]
        if 'bms' in device:
            device_id = int(device[-1])
        else:
            device_id = 0

        self._hub.start_update_log_history(device_id, log_depth)

    @property
    def name(self):
        """Return the name."""
        return f"{self._name}"

    @property
    def unique_id(self) -> Optional[str]:
        return f"{self._platform_name}_{self._key}"

    @property
    def device_info(self) -> Optional[Dict[str, Any]]:
        return self._device_info