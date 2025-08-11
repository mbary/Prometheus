# Prometheus

> In Greek mythology, Prometheus (/prəˈmiːθiəs/; Ancient Greek: Προμηθεύς, [promɛːtʰéu̯s], possibly meaning "forethought")[1] is one of the Titans and a god of fire.[2] Prometheus is best known for defying the Olympian gods by taking fire from them and giving it to humanity in the form of technology, knowledge and, more generally, civilization.

A library for controlling Philips Hue smart lighting systems through the Hue Bridge API v2.

Just like Prometheus rebelled against the gods of Olympus, by giving humanity the knowledge and ability to harness fire, I rebel against apple forcing me to purchase additional hardware to unlock the full power of the Philips Hue ecosystem.<br>
One cannot, for example, use siri to change the brightness without having to purchase additional homehub devices.<br>

**[EDIT]**<br>
Well, it turns out apple has made some changes, no longer requiring a homehub device to operate the lights (this does not work with older hue bridges though). My rebelious spirit made me write this prior to these updates so yeah, it was a fun project nonetheless.<br>

## Table of Contents
- [Why?](#why)
- [Overview](#overview)
  - [Key Features](#key-features)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Environment Variables (Recommended)](#environment-variables-recommended)
  - [YAML Configuration File](#yaml-configuration-file)
  - [Configuration Priority](#configuration-priority)
- [Quick Start](#quick-start)
- [Detailed Usage](#detailed-usage)
  - [Bridge Management](#bridge-management)
  - [Individual Light Control](#individual-light-control)
  - [Room Control](#room-control)
  - [Zone Control](#zone-control)
  - [Scene Management](#scene-management)
- [Architecture](#architecture)
  - [Class Hierarchy](#class-hierarchy)
  - [Device Discovery Flow](#device-discovery-flow)
  - [Configuration Loading](#configuration-loading)
- [Development](#development)
  - [Project Structure](#project-structure)
- [Technical Details](#technical-details)
  - [Device State Management](#device-state-management)
  - [Scene Assignment Logic](#scene-assignment-logic)
  - [Scene Priority Logic](#scene-priority-logic)
  - [Smart Room Behavior](#smart-room-behavior)
- [TODO's](#todos-1)
- [License](#license)

## Why?
The entire point of this project was a small rebelion against apple etc.<br> 
As of recently I've been playing with ai agents and I love me a challenging task so I asked myself "why not have locally running agent?" <br>
I will attempt to have a locally served voice2text model and another one that's good with tools (likely qwen3).
Due to hardware constaints (GPU poor) I will most likely be forced to use one of the smaller versions.<br>
To ensure it works well with the few tools it'll have, I'll try and RL the LIFE out of it and well see what happens.<br>
RL? Another hard project? sweet<br>
So lookout for prometheus_ai©

## Overview

Prometheus is a comprehensive Python package that provides intuitive control over Philips Hue lighting systems. It offers both individual device control and grouped operations (rooms/zones), scene management, and robust configuration handling - all through a clean, Pythonic interface.

### Key Features

- **Flexible Configuration**: YAML files, environment variables, or direct IP configuration
- **Device Management**: Control individual lights, rooms, and zones
- **Scene Control**: Activate and manage lighting scenes and smart scenes  

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd Prometheus

# Using uv (recommended)
uv sync
```

## Configuration

Prometheus supports multiple configuration methods with IP addresses preferred over hostnames for reliability.<br>
Guide how to [obtain the Hue Bridge IP address](https://developers.meethue.com/develop/hue-api-v2/getting-started/).

### Environment Variables (Recommended)

Create a `.env` file in your project directory:

```bash
# Preferred: Use IP address
HUE_IP=<your_hue_ip_address>
HUE_KEY=<your_hue_bridge_api_key>

# Alternative: Use hostname  
HUE_HOSTNAME=<your-bridge-hostname>
HUE_KEY=<your_hue_bridge_api_key>
```
or simply export them as bash environment variables

### YAML Configuration File

Create a `cfg.yaml` file:

```yaml
# Preferred: Use IP address
ip: <your_hue_ip_address>
key: "your_hue_bridge_api_key"

# Alternative: Use hostname
hostname: <your-bridge-hostname>
key: <your_hue_bridge_api_key>
```

### Configuration Priority

1. **YAML file**: `ip` field first, then `hostname` as fallback
2. **Environment variables**: `HUE_IP` first, then `HUE_HOSTNAME` as fallback
3. **Error**: Clear error message if neither method provides valid configuration

## Quick Start

```python
from Prometheus import Bridgette

# Initialize the bridge connection
bridge = Bridgette()

# Turn on all lights
bridge.turn_all_lights_on()

# Turn off all devices
bridge.turn_all_devices_off()

# Access individual lights
desk_lamp = bridge.lights['desk lamp']
desk_lamp.turn_on()
desk_lamp.change_brightness(75)

# Control rooms
office = bridge.rooms['office']
office.turn_on()  # Activates 'natural light' scene for office/bedroom
office.set_scene('relaxing')

# Control zones
living_area = bridge.zones['living area']
living_area.change_brightness(50)
living_area.set_smart_scene('cozy evening')
```

## Detailed Usage

### Bridge Management

The `Bridgette` class is your main entry point for controlling the Hue system:

```python
from Prometheus import Bridgette
from pathlib import Path

# Default configuration (looks for ./cfg.yaml, then env vars)
bridge = Bridgette()

# Custom configuration file
bridge = Bridgette(cfg_path=Path('/path/to/custom/config.yaml'))

# Access discovered devices
print(f"Found {len(bridge.lights)} lights")
print(f"Found {len(bridge.rooms)} rooms") 
print(f"Found {len(bridge.zones)} zones")
```

### Individual Light Control

Control individual Hue lights and smart plugs:

```python
# Get a specific light
bedroom_light = bridge.lights['bedroom ceiling']

# Basic controls
bedroom_light.turn_on()
bedroom_light.turn_off()

# Brightness control (0-100)
bedroom_light.change_brightness(80)

# Color temperature (153-500 mirek, warm to cool)
bedroom_light.change_temp(300)  # Neutral white

# Check current state
print(f"Light is {'on' if bedroom_light.state == 'true' else 'off'}")
print(f"Brightness: {bedroom_light.brightness_level}%")
print(f"Color temp: {bedroom_light.colour_temperature} mirek")
```

### Room Control

Rooms represent logical groupings of lights with scene support:

```python
# Get a room
kitchen = bridge.rooms['kitchen']

# Basic controls
kitchen.turn_on()   # Smart behavior: office/bedroom get 'natural light' scene
kitchen.turn_off()

# Brightness control for all lights in room
kitchen.change_brightness(60)

# Scene management
kitchen.set_scene('dinner party')
kitchen.set_scene('bright', brightness=90)

# Smart scenes (dynamic/adaptive scenes)
kitchen.set_smart_scene('energizing', brightness=75)

# Access devices
for light_name, light in kitchen.devices.items():
    print(f"{light_name}: {light.state}")
```

### Zone Control

Zones provide flexible groupings of lights across rooms:

```python
# Get a zone
downstairs = bridge.zones['downstairs']

# Similar interface to rooms
downstairs.turn_on()
downstairs.change_brightness(40)
downstairs.set_scene('movie time')
downstairs.set_smart_scene('sunset')

# Access available scenes
print("Available scenes:", list(downstairs.scenes.keys()))
```

### Scene Management

Scenes are automatically discovered and assigned to their respective rooms/zones as HueScene objects:

```python
# List all scenes for a room
office = bridge.rooms['office']
print("Office scenes:", list(office.scenes.keys()))

# Activate scenes with optional brightness override
office.set_scene('focus')           # Default brightness
office.set_scene('relax', 30)       # 30% brightness

# Smart scenes adapt throughout the day
office.set_smart_scene('natural light')
office.set_smart_scene('energizing', 85)

# Access HueScene objects directly
focus_scene = office.scenes['focus']
print(f"Scene type: {focus_scene.type}")        # 'scene' or 'smart_scene'
print(f"Scene status: {focus_scene.status}")    # 'on' or 'off'
print(f"Scene metadata: {focus_scene.metadata}")

# Turn scenes on/off directly
focus_scene.turn_on()
focus_scene.turn_off()

# Check current state of all rooms/zones including active scenes
current_state = bridge.get_current_state()
print(f"Office scene: {current_state['rooms']['office']['room_state']['scene']}")
```

## Architecture

### Class Hierarchy

```
HueResource (Base)
├── HueLight      - Individual lights and smart plugs
├── HueRoom       - Room-based device groups with scene management  
├── HueZone       - Zone-based device groups with scene management
└── HueScene      - Scene objects with status monitoring and control

Bridgette         - Main controller and bridge interface
```

### Device Discovery Flow

1. **Bridge Connection**: Connect to Hue Bridge via IP/hostname
2. **Device Discovery**: Fetch all lights, rooms, and zones
3. **Scene Assignment**: Map scenes to their respective rooms/zones
4. **Child Device Mapping**: Link individual lights to rooms/zones
5. **Ready**: All devices available for control

### Configuration Loading

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Config File   │───▶│   Environment    │───▶│   Error (Missing    │
│ ip/hostname+key │    │ HUE_IP/HOSTNAME  │    │   Configuration)    │
│                 │    │     + HUE_KEY    │    │                     │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
```



## Development

### Project Structure

```
Prometheus/
├── Prometheus/          # Main package
│   ├── __init__.py      # Package exports
│   ├── bridgette.py     # Main Bridgette class
│   ├── device.py        # Device classes (HueLight, HueRoom, HueZone)
│   ├── exceptions.py    # Custom exceptions
│   └── tests/           # Unit tests
├── README.md            # This file
├── pyproject.toml       # Project configuration
└── requirements.txt     # Dependencies
```




## Technical Details

### Device State Management

The library maintains device states through several mechanisms:

1. **Initial State Discovery**: During initialization, all devices fetch their current state from the bridge
2. **State Caching**: Device objects cache state locally to reduce API calls
3. **State Updates**: State is updated after successful operations
4. **Child Device Mapping**: Lights are automatically mapped to their parent rooms/zones

### Scene Assignment Logic

Scenes are discovered and assigned during bridge initialization:

1. **Scene Discovery**: Fetch all regular and smart scenes from the bridge
2. **HueScene Creation**: Create HueScene objects for each discovered scene
3. **Group Mapping**: Match scenes to rooms/zones based on group IDs
4. **Scene Storage**: HueScene objects are stored in the `scenes` dictionary of their parent group
5. **Case Handling**: Scene names are normalized to lowercase for consistent access
6. **Status Monitoring**: HueScene objects fetch live status data from the bridge when accessed

### Scene Priority Logic

When determining active scenes, the system follows this priority:

1. **Smart Scene Priority**: Smart scenes are checked first and take precedence
2. **Regular Scene Fallback**: Regular scenes are only considered if no smart scene is active
3. **Live Status**: All scene status checks fetch fresh data from the bridge to ensure accuracy

### Smart Room Behavior

The library includes intelligent defaults for specific rooms:

- **Office and Bedroom**: `turn_on()` automatically activates 'natural light' scene
- **Other Rooms**: `turn_on()` simply powers on all lights
- **Customizable**: This behavior can be extended for additional room types



## TODO's 
Additional functionality worth considering:
- Changing light colours
- Adding/Removing scenes
- Adding/Removing devices


## License

This project is available under the MIT License. See the LICENSE file for details.

---

*Bringing the power of fire and light to the modern smart home.*