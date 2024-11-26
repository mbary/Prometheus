import json
import os
import requests
import yaml
from pathlib import Path
from pprint import pprint

with open('cfg.yaml', 'r') as file:
    cfg = yaml.load(file, Loader=yaml.Loader)

HOSTNAME = cfg["hostname"]
HUE_KEY = cfg["key"]
BASE_URL = f'https://{HOSTNAME}'

HEADERS = {
        'hue-application-key':HUE_KEY
    ,   'Content-Type':'application/json'
}



class Bridgette:
    def  __init__(self, cfg_path:Path=Path('./cfg.yaml')) -> None:
        with open(cfg_path, 'r') as file:
            self.cfg = yaml.load(file, Loader=yaml.Loader)

        self.__HUE_HOSTNAME = self.cfg['hostname']
        self.__HUE_KEY = self.cfg["key"]
        self.__BASE_URL = f'https://{self.__HUE_HOSTNAME}/'
        self._HEADERS = {
                    'hue-application-key':self.__HUE_KEY
                ,   'Content-Type':'application/json'
        }
        self._BODY = {} 