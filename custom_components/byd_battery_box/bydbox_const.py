
INVERTER_LIST = [ "Fronius HV", "Goodwe HV/Viessmann HV", "Goodwe LV/Viessmann LV", "KOSTAL HV", "Selectronic LV", "SMA SBS3.7/5.0/6.0 HV", "SMA LV", "Victron LV", "SUNTECH LV", "Sungrow HV", "KACO_HV", "Studer LV", "SolarEdge LV", "Ingeteam HV", "Sungrow LV", "Schneider LV", "SMA SBS2.5 HV", "Solis LV", "Solis HV", "SMA STP 5.0-10.0 SE HV", "Deye LV", "Phocos LV", "GE HV", "Deye HV", "Raion LV", "KACO_NH", "Solplanet", "Western HV", "SOSEN", "Hoymiles LV", "Hoymiles HV", "SAJ HV" ]
LVS_INVERTER_LIST = {
   0: INVERTER_LIST[0], 
   1: INVERTER_LIST[1], 
   2: INVERTER_LIST[1], 
   3: INVERTER_LIST[2],  
   4: INVERTER_LIST[18],
   5: INVERTER_LIST[3],
   6: INVERTER_LIST[19],
   7: INVERTER_LIST[20],
   8: INVERTER_LIST[30],
   9: INVERTER_LIST[4],
   10: INVERTER_LIST[5],
   11: INVERTER_LIST[21],
   12: INVERTER_LIST[28],
   13: INVERTER_LIST[6],
}
HVL_INVERTER_LIST = {
   0: INVERTER_LIST[1], 
   1: INVERTER_LIST[3], 
   2: INVERTER_LIST[8], 
   3: INVERTER_LIST[10],  
   4: INVERTER_LIST[17]
}

APPLICATION_LIST = [ "Off Grid", "On Grid", "Backup" ]
PHASE_LIST = [ "Single", "Three" ]
WORKING_AREA = [ "B", "A", "B" ]

MODULE_SPECS = {
    'LVL': {'capacity': 8.68, 'cells': 0, 'sensors_t': 0},
    'LVS': {'capacity': 4, 'cells': 16, 'sensors_t': 8},
    'HVL': {'capacity': 4, 'cells': 0, 'sensors_t': 0},
    'HVM': {'capacity': 2.76, 'cells': 16, 'sensors_t': 8},
    'HVS': {'capacity': 2.56, 'cells': 32, 'sensors_t': 12},
    }

MODULE_TYPE = {
    0: "HVL",
    1: "HVM",
    2: "HVS"
}

BMU_ERRORS = {
    0: "High temperature charging (cells)",
    1: "Low temperature charging (cells)",
    2: "Discharging overcurrent(cells)",
    3: "Charging overcurrent(cells)",
    4: "Main circuit failure",
    5: "Short circuit",
    6: "Cell imbalance",
    7: "Current sensor error",
    8: "Battery overvoltage",
    9: "Battery undervoltage",
    10: "Cell overvoltage",
    11: "Cell undervoltage",
    12: "Voltage sensor failure",
    13: "Temperature sensor failure",
    14: "High temperature discharging (cells)",
    15: "Low temperature discharging (cells)",
}

BMS_ERRORS = {
    0: "Cells voltage sensor failure", 
    1: "Temperature sensor failure",   
    2: "BIC communication failure",       
    3: "Pack voltage sensor failure",   
    4: "Current sensor failure",
    5: "Charging MOS failure",
    6: "Discharging MOS failure",
    7: "Precharging MOS failure",
    8: "Main relay failure", 
    9: "Precharging Failed",
    10: "Heating device failure",
    11: "Radiator failure",
    12: "BIC balance failure",
    13: "Cells failure",
    14: "PCB temperature sensor failure", 
    15: "Functional safety failure"
}
BMS_WARNINGS = {
    0: "Battery overvoltage",
    1: "Battery undervoltage",
    2: "Cells overvoltage",
    3: "Cells undervoltage", 
    4: "Cells imbalance",
    5: "Charging high temperature (cells)",
    6: "Charging low temperature (cells)",
    7: "Discharging high temperature (cells)",
    8: "Discharging low temperature (cells)",
    9: "Charging overcurrent (cells)",
    10: "Discharging overcurrent (cells)",
    11: "Charging overcurrent (hardware)",
    12: "Short circuit",
    13: "Inverse connection",
    14: "Interlock switch abnormal",
    15: "Air switch abnormal"
}

BMS_WARNINGS3 = { 
    0: "Battery overvoltage",
    1: "Battery undervoltage",
    2: "Cell overvoltage",
    3: "Cell undervoltage",
    4: "Voltage sensor failure",
    5: "Temperature sensor failure",
    6: "High temperature discharging (cells)",
    7: "Low temperature discharging (cells)",
    8: "High temperature charging (cells)",
    9: "Low temperature charging (cells)",
    10: "Overcurrent discharging",
    11: "Overcurrent charging",
    12: "Main circuit failure",
    13: "Short circuit alarm",
    14: "Cells imbalance",
    15: "Current sensor failure" 
}

BMU_LOG_WARNINGS = {
    2: "Cells overvoltage", 
    3: "Cells undervoltage", 
    4: "V-sensor failure",  
    7: "Cell discharge temp low", 
    9: "Cell charge temp low", 
    14: "Cells imbalance",   
}

BMU_LOG_ERRORS = {
    0: "Total voltage too high", 
    1: "Total voltage too low", 
    2: "Cell voltage too high",
    3: "Cell voltage too low",
    4: "Voltage sensor fault",
    5: "Temperature sensor fault",
    6: "Cell discharging temp too high",
    7: "Cell discharging temp too low",
    8: "Cell charging temp too high",
    9: "Cell charging temp too low",
    10: "Discharging overcurrent",
    11: "Charging overcurrent", 
    12: "Major loop fault",
    13: "Short circuit warning",
    14: "Battery imbalance",
    15: "Current sensor fault",
    23: "" # No error
}

BMU_LOG_CODES = { 
	0:"Powered ON", 
	1:"Powered OFF", 
	2:"Events record", 

    22: "Firmware update started",                  
    23: "Firmware update finished",                
    24: "Firmware update fails",                  
    25: "SN code was changed",                  
    26: "Current calibration",                    
    27: "Battery voltage calibration",           
    28: "Pack voltage calibration",               
    29: "SOC/SOH calibration",                    

	32:"System status changed", 
	33:"Erase BMS firmware", 
    34:"BMS update start",                      
    35:"BMS update done",                        
	36:"Functional safety info", 

	38:"SOP info", 
	39:"BCU hardware failed", 
    40:"BMS firmware list",                   
    41:"MCU list of BMS",                    

	101:"Firmware update started", 
	102:"Firmware update finished", 
	103:"Firmware update failure", 
	104:"Firmware jump into other section", 
	105:"Parameters table updated", 
	106:"SN code changed", 

	111:"Time calibrated", 
	112:"BMS disconnected with BMU", 
	113:"BMU F/W reset", 
	114:"BMU watchdog reset", 
	115:"Precharge failed", 
	116:"Address registration failed", 
	117:"Parameters table load failed", 
	118:"System timing", 
	120:"Parameters table updating done" 
}

BMS_LOG_CODES = { 
    0:"Powered ON", 
    1:"Powered OFF", 
    2:"Events record", 
    3:"Timing record", 
    4:"Start charging", 
    5:"Stop charging", 
	6:"Start discharging", 
	7:"Stop discharging", 
    8:"SOC calibration rough", 
    9:"SOC calibration fine", 
    10:"SOC calibration stop",     
    11:"CAN communication failed", 
    12:"Serial communication failed", 
    13:"Receive precharge command", 
    14:"Precharge successful", 
    15:"Precharge failure", 
    16:"Start end SOC calibration", 
    17:"Start balancing", 
    18:"Stop balancing", 
    19:"Address registered", 
    20:"System functional safety fault", 
    21:"Events additional info", 

    101:"Firmware update started", 
    102:"Firmware update finished", 
    103:"Firmware update failed", 
    104:"Firmware jump into other section", 
    105:"Parameters table updated", 
    106:"SN code changed", 
    107:"Current calibration", 
    108:"Battery voltage calibration", 
    109:"Pack voltage calibration", 
    110:"SOC/SOH calibration", 
    111:"Time calibrated"
}

BMS_POWER_OFF = {
    0: "",                                                             
    1: "Press BMS LED button to switch off",                          
    2: "BMU requires to switch off",                                  
    3: "BMU power off and communication between BMU and BMS failed",  
    4: "Power off while communication failed(after 30 minutes)",      
    5: "Premium LV BMU requires to power off",                        
    6: "Press BMS LED to power off",                                  
    7: "Power off due to communication failed with BMU",              
    8: "BMS off due to battery undervoltage",                         
}

BMS_STATUS_ON = {
    0: "Charge MOS switch on",                      
    1: "Discharge MOS switch on",                   
    2: "Precharge MOS switch on",                   
    3: "Relay on",                                  
    4: "Air switch on",                             
    5: "Precharge 2 MOS switch on",                 
}

BMS_STATUS_OFF = {
    0: "Charge MOS switch off",                     
    1: "Discharge MOS switch off",                  
    2: "Precharge MOS switch off",                  
    3: "Relay off",                                 
    4: "Air switch off",                            
    5: "Precharge 2 MOS switch off",                
}

BMU_STATUS = {
    0: "Standby",         
    1: "Inactive",                        
    2: "Restart",  
    3: "Active",  
    4: "Fault",     
    5: "Updating", 
    6: "Shutdown",
    7: "Precharge",
    8: "Battery check",
    9: "Assign address",
    10: "Load parameters", 
    11: "Init",                                    
}

BMU_CALIBRATION = {
    0: 'computer',
    1: 'inverter',
    2: 'internet'
}

DATA_POINTS = {
    'b_cells': {'label':'Balancing cells', 'type':'nlist', 'unit':''},
    'c_max_v': {'label':'Cell max voltage', 'type':'n', 'unit':'mV'},
    'c_min_v': {'label':'Cell min voltage', 'type':'n', 'unit':'mV'},
    'c_max_t': {'label':'Cell max temp', 'type':'n', 'unit':'°C'},
    'c_min_t': {'label':'Cell min temp', 'type':'n', 'unit':'°C'},
    'c_max_v_n': {'label':'Cell max voltage id', 'type':'n', 'unit':''},
    'c_min_v_n': {'label':'Cell min voltage id', 'type':'n', 'unit':''},
    'c_max_t_n': {'label':'Cell max temp id', 'type':'n', 'unit':''},
    'c_min_t_n': {'label':'Cell min temp ud', 'type':'n', 'unit':''},
    'status': {'label':'Status', 'type':'slist', 'unit':''},
    'errors': {'label':'Errors', 'type':'slist', 'unit':''},
    'warnings': {'label':'Warnings', 'type':'slist', 'unit':''},
    'soc': {'label':'SOC', 'type':'n', 'unit':'%'},
    'soh': {'label':'SOH', 'type':'n', 'unit':'%'},
    'bat_v': {'label':'Battery voltage', 'type':'n', 'unit':'V'},
    'out_v': {'label':'Output voltage', 'type':'n', 'unit':'V'},
    'out_a': {'label':'Output current', 'type':'n', 'unit':'A'},
    'bat_idle': {'label':'Battery idling', 'type':'n', 'unit':'%'},
    'target_soc': {'label':'Target SOC', 'type':'n', 'unit':'%'},
    'bmu_serial_v1': {'label':'BMU serial v1', 'type':'n', 'unit':''},
    'bmu_serial_v2': {'label':'BMU serial v2', 'type':'n', 'unit':''},
    'rtime': {'label':'Running time', 'type':'n', 'unit':'s'},
    'bmu_qty_c': {'label':'Cells', 'type':'n', 'unit':''},
    'bmu_qty_t': {'label':'Temperature sensors', 'type':'n', 'unit':''},
    'acc_v': {'label':'Accumulated voltage', 'type':'n', 'unit':'V'},
    'bms_addr': {'label':'BMS address', 'type':'n', 'unit':''},
    'm_qty': {'label':'Modules', 'type':'n', 'unit':''},
    'm_type': {'label':'Module type', 'type':'n', 'unit':''},
    'max_charge_a': {'label':'Max charge current', 'type':'n', 'unit':'A'},
    'max_discharge_a': {'label':'Max discharge current', 'type':'n', 'unit':'A'},
    'max_charge_v': {'label':'Max charge voltage', 'type':'n', 'unit':'V'},
    'max_discharge_v': {'label':'Max discharge voltage', 'type':'n', 'unit':'V'},
    'bat_t': {'label':'Battery temp', 'type':'n', 'unit':'°C'},
    'bat_max_t': {'label':'Battery max temp', 'type':'n', 'unit':'°C'},
    'bat_min_t': {'label':'Battery min temp', 'type':'n', 'unit':'°C'},
    'inverter': {'label':'Inverter', 'type':'n', 'unit':''},
    'bms_qty': {'label':'BMS quantity', 'type':'n', 'unit':''},
    'nt': {'label':'Date time set to {v}', 'type':'s', 'unit':''},
    #'dt': {'label':'Delta t', 'type':'n', 'unit':'s'},
    'env_max_t': {'label':'Environment max temp', 'type':'n', 'unit':'°C'},
    'env_min_t': {'label':'Environment min temp', 'type':'n', 'unit':'°C'},
    'event': {'label':'Event', 'type':'n', 'unit':''},
    'n_status': {'label':'New status', 'type':'n', 'unit':''},
    'p_status': {'label':'Prev status', 'type':'n', 'unit':''},
    'firmware_n1': {'label':'Firmware n1', 'type':'n', 'unit':''},
    'firmware_v1': {'label':'Firmware v1', 'type':'n', 'unit':''},
    'firmware_n2': {'label':'Firmware n2', 'type':'n', 'unit':''},
    'firmware_v2': {'label':'Firmware v2', 'type':'n', 'unit':''},
    'firmware_n3': {'label':'Firmware n3', 'type':'n', 'unit':''},
    'firmware_v3': {'label':'Firmware v3', 'type':'n', 'unit':''},
#    'pt_u': {'label':'Parameter table update', 'type':'n', 'unit':''},
    'pt_v': {'label':'Parameter table updated to v {v}', 'type':'s', 'unit':''},
    'dt_cal': {'label':'Datetime calibration by {v}', 'type':'s', 'unit':''},
    'bms_updt': {'label':'BMS update', 'type':'n', 'unit':''},
    'firmware_v': {'label':'Firmware', 'type':'n', 'unit':''},
    'mcu': {'label':'MCU', 'type':'n', 'unit':''},
    'bootl': {'label':'Bootloader', 'type':'n', 'unit':''},
    'exec': {'label':'Executing', 'type':'n', 'unit':''},
    'switchoff': {'label':'Powered off by {v}', 'type':'s', 'unit':''},
    'area': {'label':'Target area', 'type':'n', 'unit':''},
    'firmware_p': {'label':'Prev firmware', 'type':'n', 'unit':''},
    'firmware_n': {'label':'New firmware', 'type':'n', 'unit':''},
    'threshold': {'label':'Threshold table', 'type':'n', 'unit':''},
    'sn_change': {'label':'Serial number change', 'type':'s', 'unit':''},
    'section': {'label':'Running section', 'type':'n', 'unit':''},
    'power_off': {'label':'Running section', 'type':'s', 'unit':''},
    'soc_a': {'label':'SOC A', 'type':'n', 'unit':'%'},
    'soc_b': {'label':'SOC B', 'type':'n', 'unit':'%'},
}
