"""Platform for sensor integration."""
from __future__ import annotations

import logging
from typing import Optional, Dict, Any

from homeassistant.components.sensor import (
    SensorEntity,
)
from homeassistant.const import CONF_NAME #, CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.icon import icon_for_battery_level
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import Entity
from homeassistant.core import callback

from . import HubConfigEntry
from .const import (
    BMU_SENSOR_TYPES,
    BMS_SENSOR_TYPES,
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
    hub_name = config_entry.data[CONF_NAME]

    entities = []

    for sensor_info in BMU_SENSOR_TYPES.values():
        sensor = BydBoxSensor(
            platform_name = ENTITY_PREFIX,
            hub = hub,
            device_info = hub.device_info_bmu,
            name = sensor_info[0],
            key = sensor_info[1],
            device_class = sensor_info[2],
            state_class = sensor_info[3],
            unit = sensor_info[4],
            icon = sensor_info[5],
            entity_category = sensor_info[6],
        )
        entities.append(sensor)

    towers = hub.data.get('towers')
    if not towers is None and towers > 0:
        for id in range(1,towers +1):
            for sensor_info in BMS_SENSOR_TYPES.values():
                sensor = BydBoxSensor(
                    platform_name = ENTITY_PREFIX,
                    hub = hub,
                    device_info = hub.get_device_info_bms(id),
                    name = f'BMS {id} ' + sensor_info[0],
                    key = f'bms{id}_' + sensor_info[1],
                    device_class = sensor_info[2],
                    state_class = sensor_info[3],
                    unit = sensor_info[4],
                    icon = sensor_info[5],
                    entity_category = sensor_info[6],
                )
                entities.append(sensor)

    async_add_entities(entities)
    return True

class BydBoxSensor(SensorEntity):
    """Representation of an BYD Battery Box Modbus sensor."""

    def __init__(self, platform_name, hub, device_info, name, key, device_class, state_class, unit, icon, entity_category):
        """Initialize the sensor."""
        self._platform_name = platform_name
        self._hub:Hub = hub
        self._key = key
        self._name = name
        self._unit_of_measurement = unit
        self._icon = icon
        self._device_info = device_info
        if not device_class is None:
            self._attr_device_class = device_class
        if not state_class is None:
            self._attr_state_class = state_class
        self._attr_entity_category = entity_category

    async def async_added_to_hass(self):
        """Register callbacks."""
        self._hub.async_add_hub_entity(self._modbus_data_updated)

    async def async_will_remove_from_hass(self) -> None:
        self._hub.async_remove_hub_entity(self._modbus_data_updated)

    @callback
    def _modbus_data_updated(self):
        self.async_write_ha_state()

    @callback
    def _update_state(self):
        if self._key in self._hub.data:
            self._state = self._hub.data[self._key]

            self._icon = icon_for_battery_level(
                battery_level=self.native_value, charging=False
            )

    @property
    def name(self):
        """Return the name."""
        return f"{self._name}"

    @property
    def unique_id(self) -> Optional[str]:
        return f"{self._platform_name}_{self._key}"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def icon(self):
        """Return the sensor icon."""
        return self._icon

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._key in self._hub.data:
            return self._hub.data[self._key]

    @property
    def extra_state_attributes(self):
        if 'balancing_qty' in self._key:
            return {'cell_balancing': self._hub.data.get(f'{self._key[:4]}_cell_balancing')}
        elif 'avg_c_v' in self._key:
            return {'cell_voltages': self._hub.data.get(f'{self._key[:4]}_cell_voltages')}
        elif 'avg_c_t' in self._key:
            return {'cell_temps': self._hub.data.get(f'{self._key[:4]}_cell_temps')}
        elif 'bmu_last_log' in self._key:
            return {'logs': self._hub.data.get('bmu_logs')}
        elif 'b_total' in self._key:
            return {'total_cells': self._hub.data.get(f'{self._key[:4]}_b_cells_total')}
        # elif 'last_log' in self._key:
        #     return {'logs': self._hub.data.get(f'{self._key[:4]}_logs')}

        return None

    @property
    def should_poll(self) -> bool:
        """Data is delivered by the hub"""
        return False

    @property
    def device_info(self) -> Optional[Dict[str, Any]]:
        return self._device_info




