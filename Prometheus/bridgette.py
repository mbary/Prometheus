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


## TODO Add stuff like __repr__, __str__ etc to create a pretty representation of the bridge
## And all devices connected to id :)

class Bridgette:
    def  __init__(self, cfg_path:Path=Path('./cfg.yaml'),) -> None:
        with open(cfg_path, 'r') as file:
            self.cfg = yaml.load(file, Loader=yaml.Loader)

        self.__HUE_HOSTNAME = self.cfg['hostname']
        self.__HUE_KEY = self.cfg["key"]
        self.__BASE_URL = f'https://{self.__HUE_HOSTNAME}/clip/v2/resource/'
        self._HEADERS = {
                    'hue-application-key':self.__HUE_KEY
                ,   'Content-Type':'application/json'
        }
        self.lights = self._get_lights()
        self.rooms = self._get_rooms()
        self.zones = self._get_zones()
        
        self._ROOM_MAP = {room.id:name for name,room in self.rooms.items()}
        self._ZONE_MAP = {zone.id:name for name,zone in self.zones.items()}
        self._assign_scenes()


    def _get_lights(self) -> List[Dict[str, HueLight]]:
        """ Fetches all lights' connected to te Bridge details"""

        res = requests.get(url=self.__BASE_URL+"light", 
                           headers=self._HEADERS,
                           verify=False)
        
        raw_lights = json.loads(res.text)
        
        all_lights = {dev_dict["metadata"]["name"].lower():HueLight(dev_dict=dev_dict,
                                                              hue_hostname=self.__HUE_HOSTNAME,
                                                              hue_key=self.__HUE_KEY) for dev_dict in raw_lights["data"]}
        return all_lights

    def _get_zones(self) -> List[Dict[str, HueZone]]:
        """ Fetches all zones connected to te Bridge details"""
        res = requests.get(url=self.__BASE_URL+"zone",
                           headers=self._HEADERS,
                           verify=False)
        raw_zones = json.loads(res.text)

        all_zones = {dev_dict['metadata']['name'].lower():HueZone(dev_dict=dev_dict,
                                                          hue_hostname=self.__HUE_HOSTNAME,
                                                          hue_key=self.__HUE_KEY) for dev_dict in raw_zones['data']}
        return all_zones
    
    def _get_rooms(self) -> List[Dict[str,HueRoom]]:
        """ Fetches all rooms connected to te Bridge details"""
        
        res = requests.get(url=self.__BASE_URL+'room',
                           headers=self._HEADERS,
                           verify=False)
        raw_rooms = json.loads(res.text)

        all_rooms = {dev_dict["metadata"]["name"].lower():HueRoom(dev_dict=dev_dict,
                                                          hue_hostname=self.__HUE_HOSTNAME,
                                                          hue_key=self.__HUE_KEY) for dev_dict in raw_rooms["data"]}
        return all_rooms
    
    ## TODO consider moving this to devices (zones/rooms) and pull respective scenes instead of 
    ## doing so in the 'controller' class
    def _get_scenes(self) -> List[Dict]:

        res = requests.get(url=self.__BASE_URL+"scene",
                           headers=self._HEADERS, 
                           verify=False)
        raw_scenes = json.loads(res.text)
        raw_smart_scenes = self._get_smart_scenes()
        all_raw_scenes = raw_scenes['data'] + raw_smart_scenes
        return all_raw_scenes
    
    def _get_smart_scenes(self) -> List[Dict]:
        res = requests.get(url=self.__BASE_URL+"smart_scene",
                           headers=self._HEADERS,
                           verify=False)
        raw_smart_scenes = json.loads(res.text)

        return raw_smart_scenes['data']

    def _assign_scenes(self) -> None:

        all_scenes = self._get_scenes()
        smart_scenes = self._get_smart_scenes()
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