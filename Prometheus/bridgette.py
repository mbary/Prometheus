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


from .device import HueLight,HueZone,HueScene,HueRoom



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


    def _get_lights(self) -> List[Dict[str, HueLight]]:
        """ Fetches all lights' connected to te Bridge details"""

        res = requests.get(url=self.__BASE_URL+"light", 
                           headers=self._HEADERS,
                           verify=False)
        
        raw_lights = json.loads(res.text)
        
        all_lights = {dev_dict["metadata"]["name"]:HueLight(dev_dict=dev_dict,
                                                              hue_hostname=self.__HUE_HOSTNAME,
                                                              hue_key=self.__HUE_KEY) for dev_dict in raw_lights["data"]}
        return all_lights

    def _get_zones(self) -> List[Dict]:
        """ Fetches all zones connected to te Bridge details"""
        res = requests.get(url=self.__BASE_URL+"zone",
                           headers=self._HEADERS,
                           verify=False)
        raw_zones = json.loads(res.text)

        all_zones = {dev_dict['metadata']['name']:HueZone(dev_dict=dev_dict,
                                                          hue_hostname=self.__HUE_HOSTNAME,
                                                          hue_key=self.__HUE_KEY) for dev_dict in raw_zones['data']}
        return all_zones
    
    def _get_rooms(self) -> List[Dict[str,HueRoom]]:
        """ Fetches all rooms connected to te Bridge details"""
        
        res = requests.get(url=self.__BASE_URL+'room',
                           headers=self._HEADERS,
                           verify=False)
        raw_rooms = json.loads(res.text)

        all_rooms = {dev_dict["metadata"]["name"]:HueRoom(dev_dict=dev_dict,
                                                          hue_hostname=self.__HUE_HOSTNAME,
                                                          hue_key=self.__HUE_KEY) for dev_dict in raw_rooms["data"]}
        return all_rooms
    
    def turn_all_devices_off(self) -> None:
        """Func for turning off all devices linked to the bridge"""
        for room in self.rooms.values():
            room.turn_off()