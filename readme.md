# MadVR Envy Home Assistant

This is the Home Assistant MadVR Envy Component implementing my [MadVR Envy](https://github.com/iloveicedgreentea/py-madvr) library

## Features

- Attributes for Incoming Signal, Outgoing Signal, Aspect ratio, Temperature
- HDR Flag
- Power off, standby
- Navigation Keys
- Menu
- etc

## Why use this?
Automate your theater based on Envy attributes like HDR flag, aspect ratio etc. E.x If hdr_flag = true, set JVC picture mode to XYZ. The HDR flag for the envy is broken for NZ models so this is really useful.

You can also trigger masking systems based on the aspect ratio reported by Envy

Turn off Envy via IP control

Create remotes inside HA Dashboard to send commands like Menu, Right, etc. Basically remake the remote in the UI. 

## Installation

This is currently only a custom component. Unlikely to make it into HA core because their process is just too burdensome and I strongly disagree with their deployment model for integrations.

Install HACS, then install the component by adding this as a custom repo
https://hacs.xyz/docs/faq/custom_repositories

You can also just copy all the files into your custom_components folder but then you won't get automatic updates.

### Home Assistant Setup
Add this to configuration.yaml

I recommend a scan_interval of at least 3. The integration will poll every $scan_interval seconds. 

```yaml
remote:
  - platform: madvr
    name: envy
    host: 192.168.88.38
    scan_interval: 3
```

*Note*

Because the Envy IP Control does not work if it is off or not rendering, you must manually call the remote.turn_on service.

This initiates the IP connection. You can do this from an automation like if AVR/JVC is on, call the service.

When you call the remote.turn_off service, it will shut down the Envy and also close the TCP connection.

## Automate JVC Picture Modes for HDR
```yaml
alias: JVC - Envy picture mode HDR
description: ""
trigger:
  - platform: state
    entity_id:
      - remote.envy
    attribute: hdr_flag
condition: []
action:
  - if:
      - condition: state
        entity_id: remote.envy
        attribute: hdr_flag
        state: true
    then:
      - service: remote.send_command
        data:
          command: picture_mode,user2
        target:
          entity_id: remote.nz7
  - if:
      - condition: state
        entity_id: remote.envy
        attribute: hdr_flag
        state: false
    then:
      - service: remote.send_command
        data:
          command: picture_mode,user1
        target:
          entity_id: remote.nz7
mode: single
```

## Useful Stuff

I wrote this for my NZ7 but you can change the commands to Envy commands and it will work the same way.

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
