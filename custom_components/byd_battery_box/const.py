from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.entity import EntityCategory

DOMAIN = "byd_battery_box"
INVERTER_LIST = [ "Fronius HV", "Goodwe HV/Viessmann HV", "Goodwe LV/Viessmann LV", "KOSTAL HV", "Selectronic LV", "SMA SBS3.7/5.0/6.0 HV", "SMA LV", "Victron LV", "SUNTECH LV", "Sungrow HV", "KACO_HV", "Studer LV", "SolarEdge LV", "Ingeteam HV", "Sungrow LV", "Schneider LV", "SMA SBS2.5 HV", "Solis LV", "Solis HV", "SMA STP 5.0-10.0 SE HV", "Deye LV", "Phocos LV", "GE HV", "Deye HV", "Raion LV", "KACO_NH", "Solplanet", "Western HV", "SOSEN", "Hoymiles LV", "Hoymiles HV", "SAJ HV" ]
APPLICATION_LIST = [ "Off Grid", "On Grid", "Backup" ]
PHASE_LIST = [ "Single", "Three" ]
WORKING_AREA = [ "B", "A", "B"]

MAX_MODULES = 8
BMU_INDEX = 0x0000
BMS1_INDEX = 0x0001
BMS2_INDEX = 0x0002

ERRORS = [ "Cells Voltage Sensor Failure","Temperature Sensor Failure","BIC Communication Failure","Pack Voltage Sensor Failure","Current Sensor Failure","Charging Mos Failure","DisCharging Mos Failure","PreCharging Mos Failure","Main Relay Failure","PreCharging Failed","Heating Device Failure","Radiator Failure","BIC Balance Failure","Cells Failure","PCB Temperature Sensor Failure","Functional Safety Failure" ]
WARNINGS = [ "Battery Over Voltage","Battery Under Voltage","Cells OverVoltage","Cells UnderVoltage","Cells Imbalance","Charging High Temperature(Cells)","Charging Low Temperature(Cells)","DisCharging High Temperature(Cells)","DisCharging Low Temperature(Cells)","Charging OverCurrent(Cells)","DisCharging OverCurrent(Cells)","Charging OverCurrent(Hardware)","Short Circuit","Inversly Connection","Interlock switch Abnormal","AirSwitch Abnormal" ]
WARNINGS3 = [ "Battery Over Voltage","Battery Under Voltage","Cell Over Voltage","Cell Under Voltage","Voltage Sensor Failure","Temperature Sensor Failure","High Temperature Discharging (Cells)","Low Temperature Discharging (Cells)","High Temperature Charging (Cells)","Low Temperature Charging (Cells)","Over Current Discharging","Over Current Charging","Main circuit Failure","Short Circuit Alarm","Cells ImBalance","Current Sensor Failure" ]

DEFAULT_NAME = "BYD Battery Box"
ENTITY_PREFIX = "bydb"
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_PORT = 8080
DEFAULT_UNIT_ID = 1
CONF_UNIT_ID = "unit_id"
ATTR_MANUFACTURER = "BYD"

BMU_SENSOR_TYPES = {
    "inverter": ["Inverter", "inverter", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "bmu_v": ["BMU Version", "bmu_v", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "bmu_v_A": ["BMU Version A", "bmu_v_A", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "bmu_v_B": ["BMU Version B", "bmu_v_B", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "bms_v": ["BMS Version", "bms_v", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "towers": ["Towers", "towers", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "modules": ["Modules", "modules", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "application": ["Application", "application", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "phase": ["Phase", "phase", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "error": ["Error bitmask", "error", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "capacity": ["Total Capacity", "capacity", None, None, "kWh", None, EntityCategory.DIAGNOSTIC],

    "soc": ["State of Charge", "soc", None, SensorStateClass.MEASUREMENT, "%", "mdi:battery", None],
    "bmu_temp": ["BMU Temperature", "bmu_temp", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "°C", "mdi:thermometer", None],
    "max_cell_temp": ["BMU Cell Temperature Max", "max_cell_temp", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "°C", "mdi:thermometer", None],
    "min_cell_temp": ["BMU Cell Temperature Min", "min_cell_temp", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "°C", "mdi:thermometer", None],
    "max_cell_v": ["BMU Cell Voltage Max", "max_cell_v", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:lightning-bolt", None],
    "min_cell_v": ["BMU Cell Voltage Min", "min_cell_v", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:lightning-bolt", None],
    "current": ["BMU Current", "current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "A", "mdi:lightning-bolt", None],
    "bat_voltage": ["BMU Battery Voltage", "bat_voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:lightning-bolt", None],
    "output_voltage": ["BMU Output Voltage", "output_voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:lightning-bolt", None],
    "power": ["BMU Power", "power", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "W", "mdi:lightning-bolt", None],
    "charge_lfte": ["Charge Total Energy", "charge_lfte", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, "Wh", None, None],
    "discharge_lfte": ["Discharge Total Energy", "discharge_lfte", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, "Wh", None, None],
    "efficiency": ["Efficiency", "efficiency",None, None, "%", None, None],
}

BMS_SENSOR_TYPES = {
    "max_cell_voltage": ["Maximum Cell Voltage", "max_cell_voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:lightning-bolt", None],
    "min_cell_voltage": ["Maximum Cell Voltage", "min_cell_voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:lightning-bolt", None],
    "max_cell_v": ["Maximum Cell Voltage", "max_cell_v", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:lightning-bolt", None],
    "min_cell_v": ["Minimum Cell Voltage", "min_cell_v", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:lightning-bolt", None],
    "current": ["Current", "current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "A", "mdi:lightning-bolt", None],
    "bat_voltage": ["Battery Voltage", "bat_voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:lightning-bolt", None],
    "output_voltage": ["Output Voltage", "output_voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:lightning-bolt", None],
}



