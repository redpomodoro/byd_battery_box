[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

# byd_battery_box
Home assistant Custom Component for reading data from BYD Battery Box. This integration uses a local modbus connection. 

> [!CAUTION]
> This is a work in progress project - it is still in early development stage, so there are still breaking changes possible.
>
> This is an unofficial implementation and not supported by BYD. It might stop working at any point in time.
> You are using this module (and it's prerequisites/dependencies) at your own risk. Not me neither any of contributors to this or any prerequired/dependency project are responsible for damage in any kind caused by this project or any of its prerequsites/dependencies.

# Installation
Copy contents of custom_components folder to your home-assistant config/custom_components folder or install through HACS.
After reboot of Home-Assistant, this integration can be configured through the integration setup UI.



# Usage

### Battery Management Unit

### Sensors
| Entity  | Description |
| --- | --- |

### Diagnostic
| Entity  | Description |
| --- | --- |
To come!

### Battery Management System

### Sensors
| Entity  | Description |
| --- | --- |

### Diagnostic
| Entity  | Description |
| --- | --- |
To come!

# Example Devices
![bmu](images/bmu.png?raw=true "bmu")

![bms](images/bmu.png?raw=true "bms")


![cell voltages](images/cell_voltages.png?raw=true "cell voltages")



Apex char
type: custom:apexcharts-card
apex_config:
  xaxis:
    labels:
      datetimeFormatter:
        hour: HH
graph_span: 15h
span:
  start: day
  offset: +1h
header:
  show: true
  title: Cell Voltages
yaxis:
  - decimals: 2
series:
  - entity: sensor.bms_1_cells_average_voltage
    type: column
    stroke_width: 2
    float_precision: 2
    data_generator: |
      return entity.attributes.cell_voltages.map((entry) => { 
      return [(new Date()).setHours(entry.c), entry.v];
      });


# References
https://github.com/sarnau/BYD-Battery-Box-Infos/blob/main/Read_Modbus.py
https://github.com/christianh17/ioBroker.bydhvs/blob/master/docs/byd-hexstructure.md
https://github.com/smarthomeNG/plugins/tree/develop/byd_bat
