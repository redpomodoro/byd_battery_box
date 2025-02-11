from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.entity import EntityCategory

DOMAIN = "byd_battery_box"

DEFAULT_NAME = "BYD Battery Box"
ENTITY_PREFIX = "bydb"
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_PORT = 8080
DEFAULT_UNIT_ID = 1
CONF_UNIT_ID = "unit_id"
ATTR_MANUFACTURER = "BYD"
DEFAULT_BMS_SCAN_INTERVAL = 600
CONF_BMS_SCAN_INTERVAL = "bms_scan_interval"

BMU_SENSOR_TYPES = {
    "inverter": ["Inverter", "inverter", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "bmu_v": ["BMU version", "bmu_v", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "bmu_v_A": ["BMU version A", "bmu_v_A", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "bmu_v_B": ["BMU version B", "bmu_v_B", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "bms_v": ["BMS version", "bms_v", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "towers": ["Towers", "towers", None, None, None, "mdi:counter", EntityCategory.DIAGNOSTIC],
    "modules": ["Modules", "modules", None, None, None,  "mdi:counter", EntityCategory.DIAGNOSTIC],
    "application": ["Application", "application", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "phase": ["Phase", "phase", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "errors": ["Errors", "errors", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "capacity": ["Total capacity", "capacity", None, None, "kWh", None, EntityCategory.DIAGNOSTIC],
    "param_t_v": ["Param table version", "param_t_v", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "sensors_t": ["Temperature sensors per module", "sensors_t", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "cells": ["Cells per module", "cells", None, None, None, None, EntityCategory.DIAGNOSTIC],

    "soc": ["State of charge", "soc", None, SensorStateClass.MEASUREMENT, "%", "mdi:battery", None],
    "soh": ["State of health", "soh", None, SensorStateClass.MEASUREMENT, "%", "mdi:battery", None],
    "bmu_temp": ["BMU temperature", "bmu_temp", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "°C", "mdi:thermometer", None],
    "max_cell_temp": ["BMU cell temperature max", "max_cell_temp", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "°C", "mdi:thermometer", None],
    "min_cell_temp": ["BMU cell temperature min", "min_cell_temp", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "°C", "mdi:thermometer", None],
    "max_cell_v": ["BMU cell voltage max", "max_cell_v", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:lightning-bolt", None],
    "min_cell_v": ["BMU cell voltage min", "min_cell_v", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:lightning-bolt", None],
    "current": ["BMU current", "current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "A", "mdi:lightning-bolt", None],
    "bat_voltage": ["BMU battery voltage", "bat_voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:lightning-bolt", None],
    "output_voltage": ["BMU output voltage", "output_voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:lightning-bolt", None],
    "power": ["BMU power", "power", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "W", "mdi:lightning-bolt", None],
    "charge_lfte": ["Charge total energy", "charge_lfte", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, "kWh", None, None],
    "discharge_lfte": ["Discharge total energy", "discharge_lfte", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, "kWh", None, None],
    "efficiency": ["Efficiency", "efficiency",None, None, "%", None, None],
    "updated": ["Updated", "updated",SensorDeviceClass.TIMESTAMP, None, None, None, EntityCategory.DIAGNOSTIC],
    "bmu_last_log": ["Last log", "bmu_last_log",None, None, None, None, EntityCategory.DIAGNOSTIC],
    "log_count": ["Log count", "log_count",None, None, None, None, EntityCategory.DIAGNOSTIC],
}

BMS_SENSOR_TYPES = {
    "max_c_v": ["Cell voltage max", "max_c_v", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:lightning-bolt", None],
    "min_c_v": ["Cell voltage min", "min_c_v", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:lightning-bolt", None],
    "max_c_v_id": ["Cell voltage max number", "max_c_v_id", None, None, None, None, None],
    "min_c_v_id": ["Cell voltage min number", "min_c_v_id", None, None, None, None, None],
    "max_c_t": ["Cell temperature max", "max_c_t", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "°C", "mdi:thermometer", None],
    "min_c_t": ["Cell temperature min", "min_c_t", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "°C", "mdi:thermometer", None],
    "max_c_t_id": ["Cell temperature max number", "max_c_t_id", None, None, None, None, None],
    "min_c_t_id": ["Cell temperature min number", "min_c_t_id", None, None, None, None, None],
    "soh": ["State of health", "soh", None, SensorStateClass.MEASUREMENT, "%", "mdi:battery", None],
    "soc": ["State of charge", "soc", None, SensorStateClass.MEASUREMENT, "%", "mdi:battery", None],
    "current": ["Current", "current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "A", "mdi:lightning-bolt", None],
    "bat_voltage": ["Battery voltage", "bat_voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:lightning-bolt", None],
    "output_voltage": ["Output voltage", "output_voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:lightning-bolt", None],
    "charge_lfte": ["Charge total energy", "charge_lfte", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, "kWh", None, None],
    "discharge_lfte": ["Discharge total energy", "discharge_lfte", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, "kWh", None, None],
    "efficiency": ["Efficiency", "efficiency",None, None, "%", None, None],
    "balancing_qty": ["Cells balancing", "balancing_qty",None, None, None, "mdi:counter", None],
    "warnings": ["Warnings", "warnings",None, None, None, None, EntityCategory.DIAGNOSTIC],
    "errors": ["Errors", "errors",None, None, None, None, EntityCategory.DIAGNOSTIC],
    "avg_c_v": ["Cells average voltage", "avg_c_v", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:lightning-bolt", None],
    "avg_c_t": ["Cells average temperature", "avg_c_t", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "°C", "mdi:lightning-bolt", None],
    "updated": ["Updated", "updated",SensorDeviceClass.TIMESTAMP, None, None, None, EntityCategory.DIAGNOSTIC],
    "last_log": ["Last log", "last_log",None, None, None, None, EntityCategory.DIAGNOSTIC],
    "b_total": ["Balancing total", "b_total",None, None, None, None, None],
}