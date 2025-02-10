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
    "avg_c_t": ["Cells average temperature", "avg_c_t", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "V", "mdi:lightning-bolt", None],
    "updated": ["Updated", "updated",SensorDeviceClass.TIMESTAMP, None, None, None, EntityCategory.DIAGNOSTIC],
    "last_log": ["Last log", "last_log",None, None, None, None, EntityCategory.DIAGNOSTIC],
    "b_total": ["Balancing total", "b_total",None, None, None, None, None],
}



# INVERTER_LIST = [ "Fronius HV", "Goodwe HV/Viessmann HV", "Goodwe LV/Viessmann LV", "KOSTAL HV", "Selectronic LV", "SMA SBS3.7/5.0/6.0 HV", "SMA LV", "Victron LV", "SUNTECH LV", "Sungrow HV", "KACO_HV", "Studer LV", "SolarEdge LV", "Ingeteam HV", "Sungrow LV", "Schneider LV", "SMA SBS2.5 HV", "Solis LV", "Solis HV", "SMA STP 5.0-10.0 SE HV", "Deye LV", "Phocos LV", "GE HV", "Deye HV", "Raion LV", "KACO_NH", "Solplanet", "Western HV", "SOSEN", "Hoymiles LV", "Hoymiles HV", "SAJ HV" ]
# LVS_INVERTER_LIST = {
#    0: INVERTER_LIST[0], 
#    1: INVERTER_LIST[1], 
#    2: INVERTER_LIST[1], 
#    3: INVERTER_LIST[2],  
#    4: INVERTER_LIST[18],
#    5: INVERTER_LIST[3],
#    6: INVERTER_LIST[19],
#    7: INVERTER_LIST[20],
#    8: INVERTER_LIST[30],
#    9: INVERTER_LIST[4],
#    10: INVERTER_LIST[5],
#    11: INVERTER_LIST[21],
#    12: INVERTER_LIST[28],
#    13: INVERTER_LIST[6],
# }
# HVL_INVERTER_LIST = {
#    0: INVERTER_LIST[1], 
#    1: INVERTER_LIST[3], 
#    2: INVERTER_LIST[8], 
#    3: INVERTER_LIST[10],  
#    4: INVERTER_LIST[17]
# }

# APPLICATION_LIST = [ "Off Grid", "On Grid", "Backup" ]
# PHASE_LIST = [ "Single", "Three" ]
# WORKING_AREA = [ "B", "A", "B"]

# #MAX_MODULES = 8
# #BMU_INDEX = 0x0000
# #BMS1_INDEX = 0x0001
# #BMS2_INDEX = 0x0002

# ERRORS = [ "Cells Voltage Sensor Failure","Temperature Sensor Failure","BIC Communication Failure","Pack Voltage Sensor Failure","Current Sensor Failure","Charging MOS Failure","DisCharging MOS Failure","PreCharging MOS Failure","Main Relay Failure","PreCharging Failed","Heating Device Failure","Radiator Failure","BIC Balance Failure","Cells Failure","PCB Temperature Sensor Failure","Functional Safety Failure" ]
# WARNINGS = [ "Battery Over Voltage","Battery Under Voltage","Cells OverVoltage","Cells UnderVoltage","Cells Imbalance","Charging High Temperature(Cells)","Charging Low Temperature(Cells)","DisCharging High Temperature(Cells)","DisCharging Low Temperature(Cells)","Charging OverCurrent(Cells)","DisCharging OverCurrent(Cells)","Charging OverCurrent(Hardware)","Short Circuit","Inversly Connection","Interlock switch Abnormal","AirSwitch Abnormal" ]
# WARNINGS3 = [ "Battery Over Voltage","Battery Under Voltage","Cell Over Voltage","Cell Under Voltage","Voltage Sensor Failure","Temperature Sensor Failure","High Temperature Discharging (Cells)","Low Temperature Discharging (Cells)","High Temperature Charging (Cells)","Low Temperature Charging (Cells)","Over Current Discharging","Over Current Charging","Main circuit Failure","Short Circuit Alarm","Cells ImBalance","Current Sensor Failure" ]


# BMU_LOG_WARNINGS = {
#     2: "Cells overvoltage",                            # 2
#     3: "Cells undervoltage",                           # 3
#     4: "V-sensor failure",                             # 4
#     7: "Cell discharge temp low",                      # 7
#     9: "Cell charge temp low",                         # 9
#     14: "Cells imbalance",                              # 14
# }

# BMU_LOG_ERRORS = {
#     0: "Total voltage too high",                       # 0
#     1: "Total voltage too low",                        # 1
#     2: "Cell voltage too high",                        # 2
#     3: "Cell voltage too low",                         # 3
#     4: "Voltage sensor fault",                         # 4
#     5: "Temperature sensor fault",                     # 5
#     6: "Cell discharging temp too high",              # 6
#     7: "Cell discharging temp too low",               # 7
#     8: "Cell charging temp too high",                 # 8
#     9: "Cell charging temp too low",                  # 9
#     10: "Discharging overcurrent",                     # 10
#     11: "Charging overcurrent",                        # 11
#     12: "Major loop fault",                             # 12
#     13: "Short circuit warning",                        # 13
#     14: "Battery imbalance",                            # 14
#     15: "Current sensor fault",                         # 15
#     23: "" # No error
# }

# BMU_ERRORS = [
#     "High temperature charging (cells)",
#     "Low temperature charging (cells)",
#     "Discharging overcurrent(cells)",
#     "Charging overcurrent(cells)",
#     "Main circuit failure",
#     "Short circuit",
#     "Cell imbalance",
#     "Current sensor error",
#     "Battery overvoltage",
#     "Battery undervoltage",
#     "Cell overvoltage",
#     "Cell undervoltage",
#     "Voltage sensor failure",
#     "Temperature sensor failure",
#     "High temperature discharging (cells)",
#     "Low temperature discharging (cells)",
# ]

# BMS_WARNINGS = [
#     "Battery overvoltage",                         # 0
#     "Battery undervoltage",                        # 1
#     "Cells overvoltage",                            # 2 *
#     "Cells undervoltage",                           # 3 *
#     "Cells imbalance",                              # 4 *
#     "Charging high temperature(cells)",             # 5
#     "Charging low temperature(cells)",              # 6
#     "Discharging high temperature(cells)",          # 7
#     "Discharging low temperature(cells)",           # 8
#     "Charging overcurrent(cells)",                  # 9
#     "Discharging overcurrent(cells)",               # 10
#     "Charging overcurrent(hardware)",               # 11
#     "Short circuit",                                # 12
#     "Inverse connection",                          # 13
#     "Interlock switch abnormal",                    # 14
#     "Air switch abnormal"                            # 15
# ]

# BMS_WARNINGS3 = [ 
#     "Battery overvoltage",
#     "Battery undervoltage",
#     "Cell overvoltage",
#     "Cell undervoltage",
#     "Voltage sensor failure",
#     "Temperature sensor failure",
#     "High temperature discharging (Cells)",
#     "Low temperature discharging (Cells)",
#     "High temperature charging (Cells)",
#     "Low temperature charging (Cells)",
#     "Overcurrent discharging",
#     "Overcurrent charging",
#     "Main circuit failure",
#     "Short circuit alarm",
#     "Cells imbalance",
#     "Current sensor failure" 
# ]

# BMS_ERRORS = [
#     "Cells voltage sensor failure",                 # 0 *
#     "Temperature sensor failure",                   # 1
#     "BIC communication failure",                    # 2
#     "Pack voltage sensor failure",                  # 3
#     "Current sensor failure",                       # 4
#     "Charging MOS failure",                         # 5
#     "Discharging MOS failure",                      # 6
#     "Precharging MOS failure",                      # 7
#     "Main relay failure",                           # 8
#     "Precharging Failed",                           # 9
#     "Heating device failure",                       # 10
#     "Radiator failure",                             # 11
#     "BIC balance failure",                          # 12
#     "Cells failure",                                # 13
#     "PCB temperature sensor failure",               # 14
#     "Functional safety failure"                     # 15
# ]

# BMU_LOG_CODES = { 
# 	0:"Power ON", 
# 	1:"Power OFF", 
# 	2:"Events record", 
# 	4:"Start charging", 
# 	5:"Stop charging", 
# 	6:"Start discharging", 
# 	7:"Stop discharging", 

#     17: "Start balancing",                        
#     18: "Stop balancing",        

# 	32:"System status changed", 
# 	33:"Erase BMS firmware", 
#     34:"BMS update start",                      
#     35:"BMS update done",                        
# 	36:"Functional safety info", 

# 	38:"SOP info", 
# 	39:"BCU hardware failed", 
#     40:"BMS firmware list",                   
#     41:"MCU list of BMS",                    

# 	0x65:"Firmware start to update", 
# 	0x66:"Firmware update successful", 
# 	0x67:"Firmware update failure", 
# 	0x68:"Firmware jump into other section", 
# 	0x69:"Parameters table updated", 
# 	0x6a:"SN code changed", 

# 	0x6f:"Datetime calibration", 
# 	0x70:"BMS disconnected with BMU", 
# 	0x71:"BMU F/W reset", 
# 	0x72:"BMU watchdog reset", 
# 	0x73:"Precharge failed", 
# 	0x74:"Address registration failed", 
# 	0x75:"Parameters table load failed", 
# 	0x76:"System timing log", 
# 	0x78:"Parameters table updating done" 
# }

# BMS_LOG_CODES = { 
#     0:"Powered ON", 
#     1:"Powered OFF", 
#     2:"Events record", 
#     3:"Timing record", 
#     4:"Start charging", 
#     5:"Stop charging", 
# 	6:"Start discharging", 
# 	7:"Stop discharging", 
#     8:"SOC calibration rough", 
#     9:"SOC calibration fine", 
#     10:"SOC calibration stop",     
#     0xb:"CAN communication failed", 
#     0xc:"Serial communication failed", 
#     0xd:"Receive precharge command", 
#     0xe:"Precharge successful", 
#     0xf:"Precharge failure", 
#     0x10:"Start end SOC calibration", 
#     0x11:"Start balancing", 
#     0x12:"Stop balancing", 
#     0x13:"Address registered", 
#     0x14:"System functional safety fault", 
#     0x15:"Events additional info", 
#     0x65:"Start firmware update", 
#     0x66:"Firmware update finish", 
#     0x67:"Firmware update failed", 
#     0x68:"Firmware jump into other section", 
#     0x69:"Parameters table update", 
#     0x6a:"SN code changed", 
#     0x6b:"Current calibration", 
#     0x6c:"Battery voltage calibration", 
#     0x6d:"Pack voltage calibration", 
#     0x6e:"SOC/SOH calibration", 
#     0x6f:"Time calibrated"
# }

# LOG_CODES = {
#     0: "Powered ON",                               
#     1: "Powered OFF",                              
#     2: "Events record",                          
#     3: "Timing record",                          
#     4: "Start charging",                         
#     5: "Stop charging",                          
#     6: "Start discharging",                     
#     7: "Stop discharging",                       
#     8: "SOC calibration rough",                  
#     9: "NA",                                     
#     10: "SOC calibration stop",                   
#     11: "CAN communication failed",               
#     12: "Serial communication failed",            
#     13: "Receive precharge command",              
#     14: "Precharge successful",                   
#     15: "Precharge failure",                      
#     16: "Start end SOC calibration",              
#     17: "Start balancing",                        
#     18: "Stop balancing",                         
#     19: "Address registered",                    
#     20: "System functional safety fault",         
#     21: "Events additional info",                
#     22: "Firmware update started",                  
#     23: "Firmware update finished",                
#     24: "Firmware update fails",                  
#     25: "SN code was changed",                  
#     26: "Current calibration",                    
#     27: "Battery voltage calibration",           
#     28: "Pack voltage calibration",               
#     29: "SOC/SOH calibration",                    

#     32: "System status changed",                 
#     33: "Erase BMS firmware",                    
#     34: "BMS update start",         #             
#     35: "BMS update done",            #            
#     36: "Functional safety info",    #            
#     37: "Not defined",                         
#     38: "SOP info",                            

#     40: "BMS firmware list",#                      
#     41: "MCU list of BMS",   #                    
    
#     # BCU Hardware failed
#     # Firmware Update failure 
#     # Firmware Jumpinto other section 

#     101: "Firmware update started",  
#     102: "Firmware update finished", 
                                                    
#     105: "Parameters table update",           
#     106: "SN code was changed",                 
                                                    
#     111: "Time calibrated",                   
#     112: "BMS disconnected with BMU",              
#     113: "MU F/W reset",                           
#     114: "BMU watchdog reset",                     
#     115: "Precharge failed",                       
#     116: "Address registration failed",            
#     117: "Parameters table load failed",           
#     118: "System timing log"                       
    
#     # Parameters table updating done 
# }

# DATA_POINTS = {
#     'b_cells': {'label':'Balancing cells', 'type':'list', 'unit':''},
#     'c_max_v': {'label':'Cell max voltage', 'type':'p', 'unit':'mV'},
#     'c_min_v': {'label':'Cell min voltage', 'type':'p', 'unit':'mV'},
#     'c_max_t': {'label':'Cell max temp', 'type':'p', 'unit':'°C'},
#     'c_min_t': {'label':'Cell min temp', 'type':'p', 'unit':'°C'},
#     'c_max_v_n': {'label':'Cell max voltage id', 'type':'p', 'unit':''},
#     'c_min_v_n': {'label':'Cell min voltage id', 'type':'p', 'unit':''},
#     'c_max_t_n': {'label':'Cell max temp id', 'type':'p', 'unit':''},
#     'c_min_t_n': {'label':'Cell min temp ud', 'type':'p', 'unit':''},
#     'status': {'label':'Status', 'type':'slist', 'unit':''},
#     'errors': {'label':'Errors', 'type':'slist', 'unit':''},
#     'warnings': {'label':'Warnings', 'type':'slist', 'unit':''},
#     'soc': {'label':'SOC', 'type':'p', 'unit':'%'},
#     'soh': {'label':'SOH', 'type':'p', 'unit':'%'},
#     'bat_v': {'label':'Battery voltage', 'type':'p', 'unit':'V'},
#     'out_v': {'label':'Output voltage', 'type':'p', 'unit':'V'},
#     'out_a': {'label':'Output current', 'type':'p', 'unit':'A'},
#     'bat_idle': {'label':'Battery idling', 'type':'p', 'unit':'%'},
#     'target_soc': {'label':'Target SOC', 'type':'p', 'unit':'%'},
#     'bmu_serial_v1': {'label':'BMU serial v1', 'type':'p', 'unit':''},
#     'bmu_serial_v2': {'label':'BMU serial v2', 'type':'p', 'unit':''},
#     'rtime': {'label':'Running time', 'type':'p', 'unit':'s'},
#     'bmu_qty_c': {'label':'Quantity cells', 'type':'p', 'unit':''},
#     'bmu_qty_t': {'label':'Quantity temp sensors', 'type':'p', 'unit':''},
#     'acc_v': {'label':'Accumulated voltage', 'type':'p', 'unit':'V'},
#     'bms_addr': {'label':'BMS address', 'type':'p', 'unit':''},
#     'm_qty': {'label':'Modules', 'type':'p', 'unit':''},
#     'm_type': {'label':'Module type', 'type':'p', 'unit':''},
#     'max_charge_a': {'label':'Max charge current', 'type':'p', 'unit':'A'},
#     'max_discharge_a': {'label':'Max discharge current', 'type':'p', 'unit':'A'},
#     'max_charge_v': {'label':'Max charge voltage', 'type':'p', 'unit':'V'},
#     'max_discharge_v': {'label':'Max discharge voltage', 'type':'p', 'unit':'V'},
#     'bat_t': {'label':'Battery temp', 'type':'p', 'unit':'°C'},
#     'bat_max_t': {'label':'Battery max temp', 'type':'p', 'unit':'°C'},
#     'bat_min_t': {'label':'Battery min temp', 'type':'p', 'unit':'°C'},
#     'inverter': {'label':'Inverter', 'type':'p', 'unit':''},
#     'bms_qty': {'label':'BMS quantity', 'type':'p', 'unit':''},
#     'nt': {'label':'Date time', 'type':'p', 'unit':''},
#     #'dt': {'label':'Delta t', 'type':'p', 'unit':'s'},
#     'env_max_t': {'label':'Environment max temp', 'type':'p', 'unit':'°C'},
#     'env_min_t': {'label':'Environment min temp', 'type':'p', 'unit':'°C'},
#     'event': {'label':'Event', 'type':'p', 'unit':''},
#     'n_status': {'label':'New status', 'type':'p', 'unit':''},
#     'p_status': {'label':'Prev status', 'type':'p', 'unit':''},
#     'firmware_n1': {'label':'Firmware n1', 'type':'p', 'unit':''},
#     'firmware_v1': {'label':'Firmware v1', 'type':'p', 'unit':''},
#     'firmware_n2': {'label':'Firmware n2', 'type':'p', 'unit':''},
#     'firmware_v2': {'label':'Firmware v2', 'type':'p', 'unit':''},
#     'firmware_n3': {'label':'Firmware n3', 'type':'p', 'unit':''},
#     'firmware_v3': {'label':'Firmware v3', 'type':'p', 'unit':''},
#     'pt_u': {'label':'Parameter table update', 'type':'p', 'unit':''},
#     'pt_v': {'label':'Parameter table v', 'type':'p', 'unit':''},
#     'dt_cal': {'label':'Datatime calibration by {v}', 'type':'s', 'unit':''},
#     'bms_updt': {'label':'BMS update', 'type':'p', 'unit':''},
#     'firmware_v': {'label':'Firmware', 'type':'p', 'unit':''},
#     'mcu': {'label':'MCU', 'type':'p', 'unit':''},
#     'bootl': {'label':'Bootloader', 'type':'p', 'unit':''},
#     'exec': {'label':'Executing', 'type':'p', 'unit':''},
#     'switchoff': {'label':'Powered off by {v}', 'type':'s', 'unit':''},
#     'area': {'label':'Target area', 'type':'p', 'unit':''},
#     'firmware_p': {'label':'Prev firmware', 'type':'p', 'unit':''},
#     'firmware_n': {'label':'New firmware', 'type':'p', 'unit':''},
#     'threshold': {'label':'Threshold table', 'type':'p', 'unit':''},
#     'sn_change': {'label':'Serial number change', 'type':'s', 'unit':''},
#     'section': {'label':'Running section', 'type':'p', 'unit':''},
#     'power_off': {'label':'Running section', 'type':'s', 'unit':''},
# }

# BMS_POWER_OFF = {
#     0: "",                                                             # 0
#     1: "Press BMS LED button to switch off",                          # 1
#     2: "BMU requires to switch off",                                  # 2 *
#     3: "BMU power off and communication between BMU and BMS failed",  # 3 *
#     4: "Power off while communication failed(after 30 minutes)",      # 4
#     5: "Premium LV BMU requires to power off",                        # 5
#     6: "Press BMS LED to power off",                                  # 6
#     7: "Power off due to communication failed with BMU",              # 7
#     8: "BMS off due to battery undervoltage",                         # 8
# }

# BMS_STATUS_ON = [
#     "Charge MOS switch on",                      # 0
#     "Discharge MOS switch on",                   # 1
#     "Precharge MOS switch on",                   # 2
#     "Relay on",                                  # 3 *
#     "Air switch on",                             # 4 *
#     "Precharge 2 MOS switch on",                 # 5
# ]

# BMS_STATUS_OFF = [
#     "Charge MOS switch off",                     # 0
#     "Discharge MOS switch off",                  # 1
#     "Precharge MOS switch off",                  # 2
#     "Relay off",                                 # 3 *  -> nur diesen Wert in einem Log gesehen
#     "Air switch off",                            # 4 *
#     "Precharge 2 MOS switch off",                # 5
# ]

# BMU_STATUS = {
#     0: "Standby",         
#     1: "Inactive",                                 # 1 *
#     2: "Restart",                              # 2
#     3: "Active",                                   # 3 *
#     4: "Fault",                                    # 4
#     5: "Updating",                                 # 5
#     6: "Shutdown",                                 # 6 *
#     7: "Precharge",                                # 7 *
#     8: "Battery check",                               # 8 *
#     9: "Assign address",                              # 9 *
#     10: "Load parameters",                               # 10 *
#     11: "Init",                                     # 11 *
# }

# MODULE_TYPE = {
#     0: "HVL",
#     1: "HVM",
#     2: "HVS"
# }

# BMU_CALIBRATION = {
#     0: 'computer',
#     1: 'inverter',
#     2: 'internet'
# }