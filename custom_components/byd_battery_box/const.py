from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.entity import EntityCategory

DOMAIN = "byd_battery_box"
INVERTER_LIST = [ "Fronius HV", "Goodwe HV/Viessmann HV", "Goodwe LV/Viessmann LV", "KOSTAL HV", "Selectronic LV", "SMA SBS3.7/5.0/6.0 HV", "SMA LV", "Victron LV", "SUNTECH LV", "Sungrow HV", "KACO_HV", "Studer LV", "SolarEdge LV", "Ingeteam HV", "Sungrow LV", "Schneider LV", "SMA SBS2.5 HV", "Solis LV", "Solis HV", "SMA STP 5.0-10.0 SE HV", "Deye LV", "Phocos LV", "GE HV", "Deye HV", "Raion LV", "KACO_NH", "Solplanet", "Western HV", "SOSEN", "Hoymiles LV", "Hoymiles HV", "SAJ HV" ]
APPLICATION_LIST = [ "Off Grid", "On Grid", "Backup" ]
PHASE_LIST = [ "Single", "Three" ]

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

SENSOR_TYPES = {
    # "acpower": ["AC Power", "acpower", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "W", "mdi:lightning-bolt", None],
    # "acenergy": ["AC Energy", "acenergy", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, "Wh", "mdi:lightning-bolt", None],
    # "tempcab": ["Temperature", "tempcab", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "°C", "mdi:thermometer", None],
    # "mppt1_power": ["MPPT1 Power", "mppt1_power", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "W", "mdi:solar-power", None],
    # "mppt2_power": ["MPPT2 Power", "mppt2_power", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "W", "mdi:solar-power", None],
    # "mppt3_power": ["Storage Charging Power", "mppt3_power", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "W", "mdi:home-battery", None],
    # "mppt4_power": ["Storage Discharging Power", "mppt4_power", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "W", "mdi:home-battery", None],
    # "pv_power": ["PV Power", "pv_power", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "W", "mdi:solar-power", None],
    # "storage_power": ["Storage Power", "storage_power", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "W", "mdi:home-battery", None],
    # "mppt1_lfte": ["MPPT1 Lifetime Energy", "mppt1_lfte", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, "Wh", "mdi:solar-panel", None],
    # "mppt2_lfte": ["MPPT2 Lifetime Energy", "mppt2_lfte", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, "Wh", "mdi:solar-panel", None],
    # "mppt3_lfte": ["Storage Charging Lifetime Energy", "mppt3_lfte", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, "Wh", "mdi:home-battery", None],
    # "mppt4_lfte": ["Storage Discharging Lifetime Energy", "mppt4_lfte", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, "Wh", "mdi:home-battery", None],
    # "load": ["Load", "load", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "W", "mdi:lightning-bolt", None],
#    "unit_id": ["Modbus ID", "i_unit_id", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "inverter": ["Inverter", "inverter", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "bmu1_v": ["BMU 1 Version", "bmu1_v", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "bmu2_v": ["BMU 2 Version", "bmu2_v", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "bms_v": ["BMS Version", "bms_v", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "towers": ["Towers", "towers", None, None, None, None, EntityCategory.DIAGNOSTIC],
    "modules": ["Modules", "modules", None, None, None, None, EntityCategory.DIAGNOSTIC],

    "soc": ["State of Charge", "soc", None, SensorStateClass.MEASUREMENT, "%", "mdi:battery", None],
    "bmu_temp": ["BMU Temp", "bmu_temp", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "°C", "mdi:thermometer", None],
}

METER_SENSOR_TYPES = {
    "power": ["Power", "power", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "W", "mdi:lightning-bolt", None],
    "exported": ["Exported", "exported", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, "Wh", "mdi:lightning-bolt", None],
    "imported": ["Imported", "imported", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, "Wh", "mdi:lightning-bolt", None],
    "unit_id": ["Modbus ID", "unit_id", None, None, None, None, EntityCategory.DIAGNOSTIC],
}

