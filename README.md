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

> [!IMPORTANT]
> The battery must be connected by LAN cable as the wireless connection disables itself after a timeout. The default IP address of the BYD battery is 192.168.16.254. Later firmware versions seem to support DHCP and will use the assigned IP address. In the later case you will need to look up the address. Depending on your network configuration a static route might be added.  You can test connectivity to the battery in the browser by using the batteries address for example http://192.168.16.254 and should get a login page. 

> [!IMPORTANT]
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

![cell_voltages](images/cell_voltages.png?raw=true "cell_voltages")

Voltages Table
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
              }}|{% for v in cells %}{{ v }}|

              {%- endfor %}

              {% endfor %}

              {%- endfor %}
            title: Cell Voltages in mV
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
              {% set
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

              {%- endfor %}              
            title: Cell Temperatures in °C
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
              {% set
              sensors=['sensor.bms_1_cells_balancing','sensor.bms_2_cells_balancing','sensor.bms_3_cells_balancing']%}
              {% set cell_count = int(states('sensor.cells_per_module')) %}  {%
              for u in range(1,int(states('sensor.towers'))+1)%} 

              {% set modules = state_attr(sensors[u-1],'cell_balancing')%} | BMS
              {{u}} |{% for i in range(1,cell_count+1)%}Cell {{i}}|{%- endfor %}

              |:---|{% for i in range(1,cell_count+1) %}---:|{% endfor %}

              {% for m in modules %}{% set cells =  m['b'] %}|Module {{ m['m']
              }}|{% for b in cells %}{% if b == 1%}yes{%else%}-{%endif%}|

              {%- endfor %}

              {% endfor %}

              {%- endfor %}
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
