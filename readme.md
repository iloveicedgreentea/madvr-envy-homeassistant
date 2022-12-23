# MadVR Envy Home Assistant

This is the Home Assistant MadVR Envy Component implementing my [MadVR Envy](https://github.com/iloveicedgreentea/py-madvr)

## Features

- Power (off, standby, reset, etc)
- Navigation Keys
- Menu
- etc

*Upcoming features: reading notifications into attributes, adding support for sensors for info like temperatures*


## Installation

This is currently only a custom component. Unlikely to make it into HA core because their process is just too burdensome and I strongly disagree with their deployment model for integrations.

Install HACS, then install the component by adding this as a custom repo
https://hacs.xyz/docs/faq/custom_repositories

You can also just copy all the files into your custom_components folder but then you won't get automatic updates.

### Home Assistant Setup
todo

### Adding attributes as sensors

replace nz7 with the name of your remote entity
```yaml
sensor:
  platform: template
  sensors:
    jvc_installation_mode:
        value_template: >
            {% if is_state('remote.nz7', 'on') %}
              {{ states.remote.nz7.attributes.installation_mode }}
            {% else %}
                Off
            {% endif %}
```

## Usage
todo

## Useful Stuff

I used this to re-create a remote in HA. Add the YAML to your dashboard to get a grid which resembles most of the remote. Other functions can be used via remote.send_command. See the library readme for details.

This is just an example. Add this sensor to your configuration.yml. Replace the nz7 with the name of your entity. Restart HA.

Add this to lovelace

```yaml
square: false
columns: 3
type: grid
cards:
  - type: button
    name: Power
    show_icon: false
    entity: remote.nz7
    show_state: true
    show_name: true
    icon: mdi:power
  - type: button
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        command: menu,up
      target:
        entity_id: remote.nz7
    show_name: false
    show_icon: true
    icon: mdi:arrow-up
    hold_action:
      action: none
  - type: button
    tap_action:
      action: none
    show_icon: false
    entity: sensor.jvc_low_latency
    show_name: true
    show_state: true
    name: Low Latency
    hold_action:
      action: none
  - type: button
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        command: menu,left
      target:
        entity_id: remote.nz7
    show_name: false
    icon: mdi:arrow-left
  - show_name: false
    show_icon: true
    type: button
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        command: menu, ok
      target:
        entity_id: remote.nz7
    name: OK
    icon: mdi:checkbox-blank-circle
    show_state: true
  - type: button
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        command: menu, right
      target:
        entity_id: remote.nz7
    show_name: false
    icon: mdi:arrow-right
  - type: button
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        command: menu,back
      target:
        entity_id: remote.nz7
    name: Back
    show_icon: false
  - type: button
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        command: menu,down
      target:
        entity_id: remote.nz7
    show_name: false
    icon: mdi:arrow-down
  - type: button
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        command: menu,menu
      target:
        entity_id: remote.nz7
    show_name: true
    show_icon: false
    name: Menu
    hold_action:
      action: none
  - show_name: true
    show_icon: true
    type: button
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        command: installation_mode,mode5
      target:
        entity_id: remote.nz7
    name: '17:9'
    icon: mdi:television
    show_state: false
  - show_name: true
    show_icon: true
    type: button
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        command: installation_mode,mode4
      target:
        entity_id: remote.nz7
    name: 2.4:1
    icon: mdi:television
    show_state: false
  - show_name: true
    show_icon: true
    type: button
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        command: installation_mode,mode2
      target:
        entity_id: remote.nz7
    name: IMAX
    icon: mdi:television
    show_state: false
```
