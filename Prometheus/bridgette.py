import json
import os
import sys
import requests
import yaml
from pathlib import Path
from pprint import pprint
from typing import List, Dict, Union
import warnings
warnings.filterwarnings('ignore')


from .device import HueLight,HueZone,HueRoom
from .exceptions import BridgeConfigError,BridgeConnectionError,BridgeResponseError, BridgeError


## TODO Add stuff like __repr__, __str__ etc to create a pretty representation of the bridge
## And all devices connected to id :)

class Bridgette:
    """Bridgette class for controlling Philips Hue bridge and connected devices.
    A class that provides interface for controlling Philips Hue bridge and its connected devices
    like lights, rooms and zones. It handles authentication, device discovery and scene management.
    Parameters
    ----------
    cfg_path : Path, optional
        Path to YAML configuration file containing bridge hostname and key (default is './cfg.yaml')
    Attributes
    ----------
    lights : dict
        Dictionary of all lights connected to the bridge, with light names as keys
    rooms : dict
        Dictionary of all rooms configured on the bridge, with room names as keys
    zones : dict
        Dictionary of all zones configured on the bridge, with zone names as keys
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
    Notes
    -----
    The class requires a YAML configuration file containing 'hostname' and 'key' fields
    for the Hue bridge authentication.
    """
    def  __init__(self, cfg_path:Path=Path('./cfg.yaml'),) -> None:

        try:
            
            ##TODO I will have to change this so no cfg file is required
            if not cfg_path.exists():
                raise BridgeConfigError(f"Configuration file not found at {cfg_path}")
            
            with open(cfg_path, 'r') as file:
                self.cfg = yaml.load(file, Loader=yaml.Loader)

            if 'hostname' not in self.cfg.keys() or 'key' not in self.cfg.keys():
                raise BridgeConfigError("Configuration file must contain 'hostname' and 'key' fields")
            
            self.__HUE_HOSTNAME = self.cfg['hostname']
            self.__HUE_KEY = self.cfg["key"]
            self.__BASE_URL = f'https://{self.__HUE_HOSTNAME}/clip/v2/resource/'
            self._HEADERS = {
                        'hue-application-key':self.__HUE_KEY
                    ,   'Content-Type':'application/json'
            }
            # Initialise all devices
            try:
                self.lights = self._get_lights()
                self.rooms = self._get_rooms()
                self.zones = self._get_zones()
                
                self._ROOM_MAP = {room.id:name for name,room in self.rooms.items()}
                self._ZONE_MAP = {zone.id:name for name,zone in self.zones.items()}
                self._assign_scenes()
            except Exception as e:
                raise BridgeConnectionError(f"Error connecting to bridge: {e}")
        
        except yaml.YAMLError as e:
            raise BridgeConfigError(f"Error parsing configuration file: {e}")
        except Exception as e:
            raise BridgeError(f"Error initialising Hue Bridge: {e}")
        
    def _get_lights(self) -> List[Dict[str, HueLight]]:
        """ Fetches all lights' connected to te Bridge details"""


        try:
            res = requests.get(url=self.__BASE_URL+"light", 
                            headers=self._HEADERS,
                            verify=False)
            
            if 'data' not in res.text:
                raise BridgeResponseError(f"Error fetching lights: {res.text}")
            
            raw_lights = json.loads(res.text)
            
            all_lights = {dev_dict["metadata"]["name"].lower():HueLight(dev_dict=dev_dict,
                                                                hue_hostname=self.__HUE_HOSTNAME,
                                                                hue_key=self.__HUE_KEY) for dev_dict in raw_lights["data"]}
            
            if not all_lights:
                raise BridgeResponseError("No lights found on the bridge")
            
            return all_lights

        except Exception as e:
            raise BridgeConnectionError(f"Error fetching lights: {e}")
        
    def _get_zones(self) -> List[Dict[str, HueZone]]:
        """ Fetches all zones connected to te Bridge details"""
        try:
            res = requests.get(url=self.__BASE_URL+"zone",
                            headers=self._HEADERS,
                            verify=False)
            
            if 'data' not in res.text:
                raise BridgeResponseError(f"Error fetching zones: {res.text}")
            raw_zones = json.loads(res.text)

            all_zones = {dev_dict['metadata']['name'].lower():HueZone(dev_dict=dev_dict,
                                                            hue_hostname=self.__HUE_HOSTNAME,
                                                            hue_key=self.__HUE_KEY) for dev_dict in raw_zones['data']}
            if not all_zones:
                raise BridgeResponseError("No zones found on the bridge")
            
            return all_zones
        except Exception as e:
            raise BridgeConnectionError(f"Error fetching zones: {e}")
        
    def _get_rooms(self) -> List[Dict[str,HueRoom]]:
        """ Fetches all rooms connected to te Bridge details"""
        
        try:
            res = requests.get(url=self.__BASE_URL+'room',
                            headers=self._HEADERS,
                            verify=False)
        
            if 'data' not in res.text:
                raise BridgeResponseError(f"Error fetching rooms: {res.text}")
            raw_rooms = json.loads(res.text)

            all_rooms = {dev_dict["metadata"]["name"].lower():HueRoom(dev_dict=dev_dict,
                                                            hue_hostname=self.__HUE_HOSTNAME,
                                                            hue_key=self.__HUE_KEY) for dev_dict in raw_rooms["data"]}
            
            if not all_rooms:
                raise BridgeResponseError("No rooms found on the bridge")
            return all_rooms
        except Exception as e:
            raise BridgeConnectionError(f"Error fetching rooms: {e}")

    ## TODO consider moving this to devices (zones/rooms) and pull respective scenes instead of 
    ## doing so in the 'controller' class
    def _get_scenes(self) -> List[Dict]:
        """ Fethes all scenes connected to the Bridge"""
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
        """ Fetches all smart scenes (e.g. Natural Light) connected to the Bridge"""
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
        """ Assigns scenes to respective rooms and zones"""
        all_scenes = self._get_scenes()
        for scene_dict in all_scenes:
            scene_id = scene_dict['group']['rid']
            if scene_id in self._ROOM_MAP.keys():
                self.rooms[self._ROOM_MAP[scene_id]].scenes[scene_dict['metadata']['name'].lower()] = scene_dict
            elif scene_id in self._ZONE_MAP.keys():
                self.zones[self._ZONE_MAP[scene_id]].scenes[scene_dict['metadata']['name'].lower()] = scene_dict
    
    def turn_all_devices_off(self) -> None:
        """Func for turning off all devices linked to the bridge"""
        for room in self.rooms.values():
            room.turn_off()

    def turn_all_lights_on(self) -> None:
        for light in self.lights:
            if light.dev_type != 'plug':
                light.turn_on()