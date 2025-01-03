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

> [!CAUTION]
> Note using other applications connecting to battery simulatousnely might give unexpected results. 

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


### Markdown Cards
Voltages Table
```
type: markdown
content: >-
  <table border="1">
  {% set modules = state_attr('sensor.bms_1_cells_average_voltage','cell_voltages')%}
  <tr><th>Module</th>
  {% for i in range(1,17) %}
  <th> Cell {{i}} </th>
  {%- endfor %}
  {% for m in modules %}
  <tr><td>{{ m['m'] }}</td>
  {% set cells =  m['v'] %}
  {% for v in cells %}
  <td>{{ v }}</td>
  {%- endfor %}
  </tr>
  {%- endfor %}
  </table>
title: Module Voltages
grid_options:
  columns: 24
  rows: 4
```

Temperatures Table
```
type: markdown
content: >+
  <table border="1">
  {% set modules = state_attr('sensor.bms_1_cells_average_temperature','cell_temps')%}
  <tr><th>Module</th>
  {% for i in range(1,9) %}
  <th>Sensor {{i}}</th>
  {%- endfor %}
  {% for m in modules %}
  <tr><td>{{ m['m'] }}</td>
  {% set cells =  m['t'] %}
  {% for v in cells %}
  <td>{{ v }}</td>
  {%- endfor %}
  </tr>
  {%- endfor %}
  </table>
title: Module Temperatures
grid_options:
  columns: 24
  rows: 4
```


### Apexcharts
![cell voltages](images/cell_voltages.png?raw=true "cell voltages")

```
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
      return [(new Date()).setHours(entry.c,0), entry.v];
      });
```

# Example Devices
![bmu](images/bmu.png?raw=true "bmu")

![bms](images/bms.png?raw=true "bms")


# References
https://github.com/sarnau/BYD-Battery-Box-Infos/blob/main/Read_Modbus.py
https://github.com/christianh17/ioBroker.bydhvs/blob/master/docs/byd-hexstructure.md
https://github.com/smarthomeNG/plugins/tree/develop/byd_bat
