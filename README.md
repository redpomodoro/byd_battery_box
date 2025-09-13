[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

# byd_battery_box
Home assistant Custom Component for reading data from BYD Battery Box system series like HVL, HVM, HVS, LVS. This integration uses a local modbus connection. 

> [!CAUTION]
> This is a work in progress project - it is still in early development stage, so there are still breaking changes possible.
>
> This is an unofficial implementation and not supported by BYD. It might stop working at any point in time.
> You are using this module (and it's prerequisites/dependencies) at your own risk. Not me neither any of contributors to this or any prerequired/dependency project are responsible for damage in any kind caused by this project or any of its prerequsites/dependencies.

> [!IMPORTANT]
> The battery must be connected by LAN cable as the wireless connection disables itself after a timeout. The default IP address of the BYD battery is 192.168.16.254. Later firmware versions seem to support DHCP and will use the assigned IP address. In the later case you will need to look up the address. Depending on your network configuration a static route might be added.  You can test connectivity to the battery in the browser by using the batteries address for example http://192.168.16.254 and should get a login page. 

> [!IMPORTANT]
> Note using other applications connecting to battery simulatousnely might give unexpected results. 

# Installation

## HACS (recommended) 

This card is available in [HACS](https://hacs.xyz/) (Home Assistant Community Store).

<small>*HACS is a third party community store and is not included in Home Assistant out of the box.*</small>

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=TimWeyand&repository=byd_battery_box&category=integration)

## Manual install

1. Download and copy Installation to your home-assistant config/custom_components folder.

2. After reboot of Home-Assistant, this integration can be configured through the integration setup UI.

# Data Updates
The key BMU Status data will by default refreshed 30 seconds. 

Detailed BMS data will be refreshed by default every 10 minutes.

# Log data
The log data is by default updated every 10 minutes. Log data is stored in /config/custom_components/byd_battery_box/log folder. The integration uses the json file for storage and for convenience a CSV file is being stored as well.

Use the buttons on the devices to retrieve additional log history, during the update all other data updates will be suspended. The integration writes warnings into log to see progress of the updates.


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

![log](images/log.png?raw=true "log")
```
      - type: grid
        cards:
          - type: markdown
            style: |
              ha-card {
                width: 100%;
              }
            content: >
              {% if states('sensor.log_entries') | is_number %} {% set log =
              state_attr('sensor.log_entries','log')%} | Timestamp | Unit | Code |
              Description | Details |

              |:---|:---|---:|:---|:---|

              {% for l in log %} |{{ l['ts'] }}|{{ l['u'] }}|{{ l['c'] }}|{{
              l['d'] }}|{{ l['detail'] }}|

              {% endfor %} {% endif %}
            title: Log
            grid_options:
              columns: full
              rows: auto
        column_span: 2
```

![cell_voltages](images/cell_voltages.png?raw=true "cell_voltages")

Voltages Table in mV
```
      - type: grid
        cards:
          - type: markdown
            style: |
              ha-card {
                width: 100%;
              }
            content: >
              {% if states('sensor.bms_1_cells_average_voltage') | is_number %}
              {% set
              sensors=['sensor.bms_1_cells_average_voltage','sensor.bms_2_cells_average_voltage','sensor.bms_3_cells_average_voltage']%}
              {% set cell_count = int(states('sensor.cells_per_module')) %}  {%
              for u in range(1,int(states('sensor.towers'))+1)%} 

              {% set modules = state_attr(sensors[u-1],'cell_voltages')%} | BMS
              {{u}} |{% for i in range(1,cell_count+1)%}Cell {{i}}|{%- endfor %}

              |:---|{% for i in range(1,cell_count+1) %}---:|{% endfor %}

              {% for m in modules %}{% set cells =  m['v'] %}|Module {{ m['m']
              }}|{% for v in cells %}{{ v }}|

              {%- endfor %}

              {% endfor %}

              {%- endfor %} {% endif %}
            title: Cell Voltages in mV
            grid_options:
              columns: full
              rows: auto
        column_span: 2
```
Voltages Table in V
```
      - type: grid
        cards:
          - type: markdown
            style: |
              ha-card {
                width: 100%;
              }
            content: >
              {% set
              sensors=['sensor.bms_1_cells_average_voltage','sensor.bms_2_cells_average_voltage','sensor.bms_3_cells_average_voltage']%}
              {% set cell_count = int(states('sensor.cells_per_module')) %}  {%
              for u in range(1,int(states('sensor.towers'))+1)%} 

              {% set modules = state_attr(sensors[u-1],'cell_voltages')%} | BMS
              {{u}} |{% for i in range(1,cell_count+1)%}Cell {{i}}|{%- endfor %}

              |:---|{% for i in range(1,cell_count+1) %}---:|{% endfor %}

              {% for m in modules %}{% set cells =  m['v'] %}|Module {{ m['m']
              }}|{% for v in cells %}{{ '%.3f' | format(v/1000) }}|

              {%- endfor %}

              {% endfor %}

              {%- endfor %}
            title: Cell Voltages in V
            grid_options:
              columns: full
              rows: auto
        column_span: 2
```

![cell_temperatures](images/cell_temperatures.png?raw=true "cell_temperatures")

Temperatures Table
```
      - type: grid
        cards:
          - type: markdown
            style: |
              ha-card {
                width: 100%;
              }
            content: >
              {% if states('sensor.bms_1_cells_average_temperature') | is_number
              %} {% set
              sensors=['sensor.bms_1_cells_average_temperature','sensor.bms_2_cells_average_temperature','sensor.bms_3_cells_average_temperature']%}
              {% set cell_count = int(int(states('sensor.cells_per_module')) /
              2) %}  {% for u in range(1,int(states('sensor.towers'))+1)%} 

              {% set modules = state_attr(sensors[u-1],'cell_temps')%} | BMS
              {{u}} |{% for i in range(1,cell_count+1)%}Cell
              {{i*2-1}}-{{i*2}}|{%- endfor %}

              |:---|{% for i in range(1,cell_count+1) %}---:|{% endfor %}

              {% for m in modules %}{% set cells =  m['t'] %}|Module {{ m['m']
              }}|{% for t in cells %}{{ t }}|

              {%- endfor %}

              {% endfor %}

              {%- endfor %}               {% endif %}
            title: Cell Temperatures in °C
            grid_options:
              columns: full
              rows: auto
        column_span: 2
```

![cell_balancing count](images/cell_balancing_count.png?raw=true "cell_balancing_count")

```
      - type: grid
        cards:
          - type: markdown
            style: |
              ha-card {
                width: 100%;
              }
            content: >
              {% if states('sensor.bms_1_balancing_total') | is_number %} {% set
              sensors=['sensor.bms_1_balancing_total','sensor.bms_2_balancing_total','sensor.bms_3_balancing_total']%}
              {% set cell_count = int(states('sensor.cells_per_module')) %}  {%
              for u in range(1,int(states('sensor.towers'))+1)%} 

              {% set modules = state_attr(sensors[u-1],'total_cells')%} | BMS
              {{u}} |{% for i in range(1,cell_count+1)%}Cell {{i}}|{%- endfor %}

              |:---|{% for i in range(1,cell_count+1) %}---:|{% endfor %}

              {% for m in modules %}{% set cells =  m['bct'] %}|Module {{ m['m']
              }}|{% for v in cells %}{{ v }}|

              {%- endfor %}

              {% endfor %}

              {%- endfor %} {% endif %}
            title: Cell Balancing Totals
            grid_options:
              columns: full
              rows: auto
        column_span: 2
```

![cell_balancing](images/cell_balancing.png?raw=true "cell_balancing")

```
      - type: grid
        cards:
          - type: markdown
            style: |
              ha-card {
                width: 100%;
              }
            content: >
              {% if states('sensor.bms_1_cells_balancing') | is_number %} {% set
              sensors=['sensor.bms_1_cells_balancing','sensor.bms_2_cells_balancing','sensor.bms_3_cells_balancing']%}
              {% set cell_count = int(states('sensor.cells_per_module')) %}  {%
              for u in range(1,int(states('sensor.towers'))+1)%} 

              {% set modules = state_attr(sensors[u-1],'cell_balancing')%} | BMS
              {{u}} |{% for i in range(1,cell_count+1)%}Cell {{i}}|{%- endfor %}

              |:---|{% for i in range(1,cell_count+1) %}---:|{% endfor %}

              {% for m in modules %}{% set cells =  m['b'] %}|Module {{ m['m']
              }}|{% for b in cells %}{% if b == 1%}on{%else%}-{%endif%}|

              {%- endfor %}

              {% endfor %}

              {%- endfor %} {% endif %}
            title: Cells Balancing
            grid_options:
              columns: full
              rows: auto
        column_span: 2

```


# Example Devices
![bmu](images/bmu.png?raw=true "bmu")

![bms](images/bms.png?raw=true "bms")


# References
https://github.com/sarnau/BYD-Battery-Box-Infos/blob/main/Read_Modbus.py
https://github.com/christianh17/ioBroker.bydhvs/blob/master/docs/byd-hexstructure.md
https://github.com/smarthomeNG/plugins/tree/develop/byd_bat
