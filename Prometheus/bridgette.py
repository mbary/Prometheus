import json
import os
import sys
import requests
import yaml
from pathlib import Path
from pprint import pprint
from typing import List, Dict, Union
import warnings
from dotenv import load_dotenv
warnings.filterwarnings('ignore')


from .device import HueLight,HueZone,HueRoom
from .exceptions import BridgeConfigError,BridgeConnectionError,BridgeResponseError, BridgeError


## TODO Add stuff like __repr__, __str__ etc to create a pretty representation of the bridge
## And all devices connected to id :)

class Bridgette:
    """Bridgette class for controlling Philips Hue bridge and connected devices.
    A class that provides interface for controlling Philips Hue bridge and its connected devices
    like lights, rooms and zones. It handles authentication, device discovery and scene management.
    
    The class supports flexible configuration loading from either YAML files or environment variables.
    
    Parameters
    ----------
    cfg_path : Path, optional
        Path to YAML configuration file containing bridge hostname and key (default is './cfg.yaml')
        If the file doesn't exist, the class will attempt to load configuration from environment variables
    Attributes
    ----------
    lights : dict
        Dictionary of all lights connected to the bridge, with light IDs as keys
    lights_by_name : dict
        Helper dictionary mapping light names to light objects (handles duplicates)
    rooms : dict
        Dictionary of all rooms configured on the bridge, with room IDs as keys
    rooms_by_name : dict
        Helper dictionary mapping room names to room objects
    zones : dict
        Dictionary of all zones configured on the bridge, with zone IDs as keys
    zones_by_name : dict
        Helper dictionary mapping zone names to zone objects
    _ROOM_MAP : dict
        Internal mapping of room IDs to room names
    _ZONE_MAP : dict
        Internal mapping of zone IDs to zone names
    __HUE_HOSTNAME : str
        Hostname of the Hue bridge
    __HUE_KEY : str
        Authentication key for the Hue bridge
    __BASE_URL : str
        Base URL for the Hue bridge API
    _HEADERS : dict
        HTTP headers used for API requests
    Methods
    -------
    _load_bridge_config(cfg_path)
        Loads bridge configuration with IP preference over hostname
    _get_lights()
        Fetches all lights connected to the bridge
    _get_zones()
        Fetches all zones configured on the bridge
    _get_rooms()
        Fetches all rooms configured on the bridge
    _get_scenes()
        Fetches all scenes configured on the bridge
    _get_smart_scenes()
        Fetches all smart scenes configured on the bridge
    _assign_scenes()
        Assigns scenes to their respective rooms and zones
    turn_all_devices_off()
        Turns off all devices connected to the bridge
    turn_all_lights_on()
        Turns on all lights (excluding plugs) connected to the bridge
    Raises
    ------
    BridgeConfigError
        If configuration cannot be loaded from file or environment variables, or if configuration is invalid
    BridgeConnectionError
        If unable to connect to or fetch data from the bridge
    BridgeResponseError
        If bridge response is invalid or no devices/scenes found
    BridgeError
        For general bridge-related errors
    yaml.YAMLError
        If YAML configuration file is malformed
    Notes
    -----
    The class supports multiple configuration methods with IP preference:
    1. YAML configuration file with 'ip' (or 'hostname') and 'key' fields (if file exists)
    2. Environment variables: HUE_IP (preferred) or HUE_HOSTNAME, and HUE_KEY (loaded via python-dotenv)
    3. Raises BridgeConfigError if neither method provides valid configuration
    
    Environment variables can be set in a .env file or system environment.
    
    IP addresses are preferred over hostnames to avoid DNS resolution issues
    common in WSL environments where /etc/hosts entries are lost after reboots.
    """
    def _load_bridge_config(self, cfg_path: Path = Path('./cfg.yaml')) -> tuple[str, str]:
        """
        Load bridge configuration from file or environment variables.
        
        This method attempts to load the Hue bridge address and key with IP preference:
        1. From the specified configuration file (if it exists) 
        2. From environment variables: HUE_IP first, then HUE_HOSTNAME as fallback
        3. Raises BridgeConfigError if neither method succeeds
        
        Parameters
        ----------
        cfg_path : Path, optional
            Path to YAML configuration file (default is './cfg.yaml')
            
        Returns
        -------
        tuple[str, str]
            A tuple containing (ip_or_hostname, key) for the Hue bridge
            
        Raises
        ------
        BridgeConfigError
            If configuration cannot be loaded from file or environment variables
        """
        load_dotenv()

        if cfg_path.exists():
            try:
                with open(cfg_path, 'r') as file:
                    cfg = yaml.load(file, Loader=yaml.Loader)

                bridge_address = cfg.get('ip') or cfg.get('hostname')
                key = cfg.get('key')
                
                if bridge_address and key:
                    return bridge_address, key
                else:
                    raise BridgeConfigError("Configuration file must contain 'ip' (or 'hostname') and 'key' fields")
                    
            except yaml.YAMLError as e:
                raise BridgeConfigError(f"Error parsing configuration file: {e}")

        bridge_address = os.getenv('HUE_IP') or os.getenv('HUE_HOSTNAME')
        key = os.getenv('HUE_KEY')
        
        if bridge_address and key:
            return bridge_address, key

        missing_vars = []
        if not bridge_address:
            missing_vars.append('HUE_IP or HUE_HOSTNAME')
        if not key:
            missing_vars.append('HUE_KEY')
            
        raise BridgeConfigError(
            f"Bridge configuration not found. Either provide a valid config file at '{cfg_path}' "
            f"with 'ip' (or 'hostname') and 'key' fields, or set environment variables: {', '.join(missing_vars)}"
        )


    def  __init__(self, cfg_path:Path=Path('./cfg.yaml'),) -> None:

        try:
            self.__HUE_ADDRESS, self.__HUE_KEY = self._load_bridge_config(cfg_path)
            self.__BASE_URL = f'https://{self.__HUE_ADDRESS}/clip/v2/resource/'
            self._HEADERS = {
                        'hue-application-key':self.__HUE_KEY
                    ,   'Content-Type':'application/json'
            }

            try:
                self.lights = self._get_lights() 
                self.rooms = self._get_rooms() 
                self.zones = self._get_zones() 
                
                self._ROOM_MAP = {room.id:room.name for room in self.rooms.values()}
                self._ZONE_MAP = {zone.id:zone.name for zone in self.zones.values()}
                self._assign_scenes()
                self._assign_devices()
            except Exception as e:
                raise BridgeConnectionError(f"Error connecting to bridge: {e}")
        
        except yaml.YAMLError as e:
            raise BridgeConfigError(f"Error parsing configuration file: {e}")
        except Exception as e:
            raise BridgeError(f"Error initialising Hue Bridge: {e}")
        
    def _get_lights(self) -> List[Dict[str, HueLight]]:
        """ Fetches all lights' connected to te Bridge details
        Returns:
            List[Dict[str, HueLight]]: Dictionary where key is light ID and value is HueLight object
        Raises:
            BridgeResponseError: If no lights are found or response format is invalid
            BridgeConnectionError: If there is an error connecting to or getting data from the bridge
        """
        try:
            res = requests.get(url=self.__BASE_URL+"light", 
                            headers=self._HEADERS,
                            verify=False)
            
            if 'data' not in res.text:
                raise BridgeResponseError(f"Error fetching lights: {res.text}")
            
            raw_lights = json.loads(res.text)
            
            all_lights = {dev_dict["id"]:HueLight(dev_dict=dev_dict,
                                                                hue_hostname=self.__HUE_ADDRESS,
                                                                hue_key=self.__HUE_KEY) for dev_dict in raw_lights["data"]}
            
            if not all_lights:
                raise BridgeResponseError("No lights found on the bridge")
            
            return all_lights

        except Exception as e:
            raise BridgeConnectionError(f"Error fetching lights: {e}")
        
    def _get_zones(self) -> List[Dict[str, HueZone]]:
        """Retrieves all zones from the Hue Bridge.
        This method queries the Hue Bridge API for all available zones and creates
        HueZone objects for each zone found.
        Returns:
            List[Dict[str, HueZone]]: A dictionary mapping zone names to HueZone objects
        Raises:
            BridgeResponseError: If no zones are found or the Bridge response is invalid
            BridgeConnectionError: If there's an error connecting to or communicating with the Bridge
        """

        try:
            res = requests.get(url=self.__BASE_URL+"zone",
                            headers=self._HEADERS,
                            verify=False)
            
            if 'data' not in res.text:
                raise BridgeResponseError(f"Error fetching zones: {res.text}")
            raw_zones = json.loads(res.text)

            all_zones = {dev_dict["metadata"]["name"].lower():HueZone(dev_dict=dev_dict,
                                                            hue_hostname=self.__HUE_ADDRESS,
                                                            hue_key=self.__HUE_KEY) for dev_dict in raw_zones['data']}
            if not all_zones:
                raise BridgeResponseError("No zones found on the bridge")
            
            return all_zones
        except Exception as e:
            raise BridgeConnectionError(f"Error fetching zones: {e}")
        
    def _get_rooms(self) -> List[Dict[str,HueRoom]]:
        """
        Retrieves all rooms configured on the Philips Hue Bridge.
        Returns:
            List[Dict[str,HueRoom]]: Dictionary mapping room names to HueRoom objects
        Raises:
            BridgeResponseError: If no rooms are found or bridge returns invalid response
            BridgeConnectionError: If there is an error connecting to or communicating with the bridge
        """
        try:
            res = requests.get(url=self.__BASE_URL+'room',
                            headers=self._HEADERS,
                            verify=False)
        
            if 'data' not in res.text:
                raise BridgeResponseError(f"Error fetching rooms: {res.text}")
            raw_rooms = json.loads(res.text)

            all_rooms = {dev_dict["metadata"]["name"].lower():HueRoom(dev_dict=dev_dict,
                                                            hue_hostname=self.__HUE_ADDRESS,
                                                            hue_key=self.__HUE_KEY) for dev_dict in raw_rooms["data"]}
            
            if not all_rooms:
                raise BridgeResponseError("No rooms found on the bridge")
            return all_rooms
        except Exception as e:
            raise BridgeConnectionError(f"Error fetching rooms: {e}")

    ## TODO consider moving this to devices (zones/rooms) and pull respective scenes instead of 
    ## doing so in the 'controller' class
    def _get_scenes(self) -> List[Dict]:
        """
        Retrieves all scenes (both regular and smart scenes) from the Hue Bridge.
        Returns:
            List[Dict]: A list of dictionaries containing scene information.
        Raises:
            BridgeResponseError: If no scenes are found or if the bridge response is invalid.
            BridgeConnectionError: If there is an error connecting to or fetching data from the bridge.
        """
        try:
            res = requests.get(url=self.__BASE_URL+"scene",
                            headers=self._HEADERS, 
                            verify=False)
            if 'data' not in res.text:
                raise BridgeResponseError(f"Error fetching scenes: {res.text}")
            raw_scenes = json.loads(res.text)
            raw_smart_scenes = self._get_smart_scenes()
            all_raw_scenes = raw_scenes['data'] + raw_smart_scenes

            if not all_raw_scenes:
                raise BridgeResponseError("No scenes found on the bridge")
            
            return all_raw_scenes
        except Exception as e:
            raise BridgeConnectionError(f"Error fetching scenes: {e}")

    def _get_smart_scenes(self) -> List[Dict]:
        """
        Retrieves smart scenes from the Philips Hue Bridge.
        Returns:
            List[Dict]: A list of dictionaries containing smart scene data from the bridge
        Raises:
            BridgeResponseError: If the bridge response is invalid or no smart scenes are found
            BridgeConnectionError: If there is an error connecting to or fetching data from the bridge
        """
        try:
            res = requests.get(url=self.__BASE_URL+"smart_scene",
                            headers=self._HEADERS,
                            verify=False)
            if 'data' not in res.text:
                raise BridgeResponseError(f"Error fetching smart scenes: {res.text}")
            raw_smart_scenes = json.loads(res.text)

            if not raw_smart_scenes:
                raise BridgeResponseError("No smart scenes found on the bridge")
            
            return raw_smart_scenes['data']
        except Exception as e:
            raise BridgeConnectionError(f"Error fetching smart scenes: {e}")


    def _assign_scenes(self) -> None:
        """
        Assigns scenes to their corresponding rooms and zones.

        This method processes all scenes retrieved from the bridge and assigns them to the appropriate
        room or zone objects based on the scene's group ID (rid). The scenes are stored in the scenes 
        dictionary of each room/zone object, with the scene name (converted to lowercase) as the key.

        The method uses _ROOM_MAP and _ZONE_MAP to determine where each scene belongs. If a scene's
        group ID matches an entry in either map, the scene is assigned to the corresponding room or zone.

        Returns:
            None
        """
        all_scenes = self._get_scenes()
        for scene_dict in all_scenes:
            scene_id = scene_dict['group']['rid']
            if scene_id in self._ROOM_MAP.keys():

                room_name = self._ROOM_MAP[scene_id]
                self.rooms[room_name].scenes[scene_dict['metadata']['name'].lower()] = scene_dict
            elif scene_id in self._ZONE_MAP.keys():

                zone_name = self._ZONE_MAP[scene_id]
                self.zones[zone_name].scenes[scene_dict['metadata']['name'].lower()] = scene_dict
    
    def _assign_devices(self) -> None:
        """
        Assigns device objects to their corresponding rooms and zones.

        This method processes all lights and maps them to the appropriate room or zone
        objects based on the light's owner device ID. The lights are stored in the 
        devices dictionary of each room/zone object, with the light name (lowercase) as the key.

        The method matches light._dev_data['owner']['rid'] with the device IDs stored in 
        room/zone.children to establish the relationship between physical devices and their
        containing spaces.

        Returns:
            None
        """

        for room in self.rooms.values():
            for child_device_id in room.children:
                for _, light_obj in self.lights.items():
                    if light_obj._dev_data.get('owner', {}).get('rid') == child_device_id:
                        room.devices[light_obj.name] = light_obj

        for zone in self.zones.values():
            for child_id in zone.children:
                for _, light_obj in self.lights.items():
                    if light_obj.id == child_id:
                        zone.devices[light_obj.name] = light_obj
                    elif light_obj._dev_data.get('owner', {}).get('rid') == child_id:
                        zone.devices[light_obj.name] = light_obj
    
    
    def turn_all_lights_off(self) -> None:
        for room in self.rooms.values():
            room.turn_off()

    def turn_all_lights_on(self) -> None:
        for light in self.lights.values():
            if light.dev_type != 'plug':
                light.turn_on()

    def get_current_state(self) -> Dict[str, Dict]:
        """
        Returns a dictionary with the current state of all devices/rooms/zones connected to the bridge.
        
        Returns:
            Dict[str, Dict]: Dictionary with the following structure:
                {
                    'zones': {
                        'zone1': {
                            'zone_state': {'state': 'on'/'off', 'scene': None/current_scene},
                            'devices': {
                                'device1': {'state': 'on'/'off', 'brightness': int, 'colour_temperature': int},
                                'device2': {...}
                            }
                        },
                        'zone2': {...}
                    },
                    'rooms': {
                        'room1': {
                            'room_state': {'state': 'on'/'off', 'scene': None/current_scene},
                            'devices': {
                                'device1': {'state': 'on'/'off', 'brightness': int, 'colour_temperature': int},
                                'device2': {...}
                            }
                        },
                        'room2': {...}
                    }
                }
        """
        current_state = {
            'zones': {},
            'rooms': {}
        }
        for zone_name, zone_obj in self.zones.items():
            zone_obj.state = zone_obj._get_state()
            
            current_state['zones'][zone_name] = {
                'zone_state': {
                    'state': 'on' if zone_obj.state.lower() == 'true' else 'off',
                    'scene': self._get_active_scene_for_group(zone_obj)
                },
                'devices': self._get_devices_state(zone_obj.devices)
            }

        for room_name, room_obj in self.rooms.items():
            room_obj.state = room_obj._get_state()
            
            current_state['rooms'][room_name] = {
                'room_state': {
                    'state': 'on' if room_obj.state.lower() == 'true' else 'off',
                    'scene': self._get_active_scene_for_group(room_obj)
                },
                'devices': self._get_devices_state(room_obj.devices)
            }
        
        return current_state

    def _get_active_scene_for_group(self, room_or_zone_obj) -> Union[str, None]:
        """
        Gets the currently active scene (regular or smart) for a room or zone.
        
        Args:
            room_or_zone_obj: HueRoom or HueZone object
            
        Returns:
            Union[str, None]: Name of active scene or None if no scene is active
        """
        try:
            for scene_name, scene_data in room_or_zone_obj.scenes.items():
                scene_id = scene_data['id']
                scene_type = scene_data.get('type', 'scene')

                scene_url = room_or_zone_obj.base_url + f"{scene_type}/{scene_id}"
                fresh_scene_response = room_or_zone_obj._get(scene_url)
                
                if fresh_scene_response.get('data') and len(fresh_scene_response['data']) > 0:
                    fresh_scene_data = fresh_scene_response['data'][0]

                    if scene_type == 'scene':
                        if fresh_scene_data.get('status', {}).get('active') != 'inactive':
                            return scene_name

                    elif scene_type == 'smart_scene':
                        if fresh_scene_data.get('state') != 'inactive':
                            return scene_name
            
            return None
        except Exception:
            return None

    def _get_devices_state(self, devices_dict: Dict) -> Dict[str, Dict]:
        """
        Extracts current state information for all devices in a collection.
        
        Args:
            devices_dict: Dictionary mapping device names to HueLight objects
            
        Returns:
            Dict[str, Dict]: Dictionary mapping device names to their current state information
        """
        devices_state = {}
        
        for device_name, device_obj in devices_dict.items():
            try:
                fresh_state = device_obj._initialise_state()
                
                device_state = {
                    'state': 'on' if fresh_state.is_on else 'off'
                }

                if not device_obj._is_plug:
                    device_state['brightness'] = fresh_state.brightness
                    device_state['colour_temperature'] = fresh_state.colour_temp
                
                devices_state[device_name] = device_state
                
            except Exception:
                device_state = {
                    'state': 'on' if device_obj.state == 'true' else 'off'
                }
                
                if not device_obj._is_plug:
                    device_state['brightness'] = device_obj.brightness_level
                    device_state['colour_temperature'] = device_obj.colour_temperature
                
                devices_state[device_name] = device_state
        
        return devices_state