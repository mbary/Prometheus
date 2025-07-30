# Prometheus

> In Greek mythology, Prometheus (/prəˈmiːθiəs/; Ancient Greek: Προμηθεύς, [promɛːtʰéu̯s], possibly meaning "forethought")[1] is one of the Titans and a god of fire.[2] Prometheus is best known for defying the Olympian gods by taking fire from them and giving it to humanity in the form of technology, knowledge and, more generally, civilization.

A library for controlling Philips Hue smart lighting systems through the Hue Bridge API v2.

Just like Prometheus rebelled against the gods of Olympus, by giving humanity the knowledge and ability to harness fire, I rebel against apple forcing me to purchase additional hardware to unlock the full power of the Philips Hue ecosystem.<br>
One cannot, for example, use siri to change the brightness without having to purchase additional homehub devices.<br>

**[EDIT]**<br>
Well, it turns out apple has made some changes, no longer requiring a homehub device to operate the lights (this does not work with older hue bridges though). My rebelious spirit made me write this prior to these updates so yeah, it was a fun project nonetheless.<br>


## Overview

Prometheus is a comprehensive Python package that provides intuitive control over Philips Hue lighting systems. It offers both individual device control and grouped operations (rooms/zones), scene management, and robust configuration handling - all through a clean, Pythonic interface.

### Key Features

- **Flexible Configuration**: YAML files, environment variables, or direct IP configuration
- **Device Management**: Control individual lights, rooms, and zones
- **Scene Control**: Activate and manage lighting scenes and smart scenes  
- **WSL-Friendly**: IP-first configuration to avoid DNS resolution issues
- **Modern API**: Built on Philips Hue Bridge API v2
- **Robust Error Handling**: Comprehensive exception hierarchy
- **Well Documented**: Type hints and detailed docstrings
- **Tested**: Comprehensive unit test coverage

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

# Access child devices
for light_name, light in kitchen.child_devices.items():
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

Scenes are automatically discovered and assigned to their respective rooms/zones:

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
```

## Architecture

### Class Hierarchy

```
HueResource (Base)
├── HueLight      - Individual lights and smart plugs
├── HueRoom       - Room-based device groups with scene management  
└── HueZone       - Zone-based device groups with scene management

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

## Advanced Features

### Custom HTTP Client

```python
import requests
from Prometheus.device import HueLight

# Custom session with specific settings
session = requests.Session()
session.timeout = 30

# Pass to device constructor (internal use)
light = HueLight(device_data, "192.168.0.122", "api_key", http_client=session)
```

### Error Handling

Prometheus provides a comprehensive exception hierarchy:

```python
from Prometheus import Bridgette
from Prometheus.exceptions import (
    BridgeConfigError, BridgeConnectionError, 
    BridgeResponseError, HueConnectionError
)

try:
    bridge = Bridgette()
    bridge.lights['nonexistent'].turn_on()
    
except BridgeConfigError as e:
    print(f"Configuration issue: {e}")
    
except BridgeConnectionError as e:
    print(f"Network/connection problem: {e}")
    
except BridgeResponseError as e:
    print(f"Invalid bridge response: {e}")
    
except HueConnectionError as e:
    print(f"Device communication error: {e}")
    
except KeyError:
    print("Device not found")
```

### Device State Monitoring

```python
# Monitor device states
for name, light in bridge.lights.items():
    current_state = light._current_state
    print(f"{name}:")
    print(f"  On: {current_state.is_on}")
    print(f"  Brightness: {current_state.brightness}")
    print(f"  Color Temp: {current_state.colour_temp}")
    print(f"  Reachable: {current_state.reachable}")
    print(f"  Last Updated: {current_state.last_updated}")
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

### Adding New Features

1. **Device Classes**: Extend `HueResource` for new device types
2. **Bridge Methods**: Add new methods to `Bridgette` for bridge-level operations
3. **Error Handling**: Use appropriate exceptions from `exceptions.py`
4. **Testing**: Add unit tests for new functionality

## API Reference

### Bridgette Class

| Method | Description |
|--------|-------------|
| `__init__(cfg_path)` | Initialize bridge connection |
| `turn_all_devices_off()` | Turn off all connected devices |
| `turn_all_lights_on()` | Turn on all lights (excluding plugs) |

**Properties:**
- `lights`: Dictionary of HueLight objects
- `rooms`: Dictionary of HueRoom objects  
- `zones`: Dictionary of HueZone objects

### HueLight Class

| Method | Parameters | Description |
|--------|-----------|-------------|
| `turn_on()` | None | Turn the light on |
| `turn_off()` | None | Turn the light off |
| `change_brightness(level)` | `level: int` (0-100) | Set brightness level |
| `change_temp(temp)` | `temp: int` (153-500) | Set color temperature |

### HueRoom/HueZone Classes

| Method | Parameters | Description |
|--------|-----------|-------------|
| `turn_on()` | None | Turn on room/zone |
| `turn_off()` | None | Turn off room/zone |
| `change_brightness(level)` | `level: int` (0-100) | Set brightness for all lights |
| `set_scene(name, brightness)` | `name: str`, `brightness: int` | Activate scene |
| `set_smart_scene(name, brightness)` | `name: str`, `brightness: int` | Activate smart scene |

## Troubleshooting

### Common Issues

**WSL DNS Resolution Problems**
```
Error: Failed to resolve '<hue_hostname>'
Solution: Use HUE_IP environment variable instead of HUE_HOSTNAME
```

**Bridge Not Found**
```
Error: Bridge configuration not found
Solution: Set HUE_IP and HUE_KEY environment variables or create cfg.yaml
```

**Device Not Responding**
```
Error: Failed to connect to Hue Bridge
Solution: Check bridge IP address and ensure it's on the same network
```

## Dependencies

- **Python**: >=3.12
- **requests**: HTTP client for API communication
- **pyyaml**: YAML configuration file parsing
- **python-dotenv**: Environment variable loading
- **pytest**: Testing framework

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
2. **Group Mapping**: Match scenes to rooms/zones based on group IDs
3. **Scene Storage**: Scenes are stored in the `scenes` dictionary of their parent group
4. **Case Handling**: Scene names are normalized to lowercase for consistent access

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