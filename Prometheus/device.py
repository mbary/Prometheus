"""
This file contains the base class for all hue resources - HueResource
Alongside major devices such as: 

"""

## TODO Add stuff like __repr__, __str__ etc to create a pretty representatoin of the devices

import json
import requests
from typing import Dict
from pprint import pprint
import warnings
warnings.filterwarnings('ignore')

class HueResource:
    ## TODO
    ## This is meant to be a Hue resource base class.
    ## It should have all attributes/capabilites shared across the HUE ecosystem
    ## Attrs: rid, rtype, product data etc.
    ## methods such as get/put etc
    ## in innit, there should be a func that automatically parses a dictionary


    ## based on this, using inheritence, we can create subclasses such as lights, switches, zones, rooms etc.
    ## They will be extended by device-specific functionalities such as on/off and whatever the fuck else I manage to find
    def __init__(self, dev_dict:Dict, hue_hostname: str, hue_key: str) -> None:
        self._hue_hostname = hue_hostname 
        self._hue_key = hue_key
        self.base_url = f"https://{self._hue_hostname}/clip/v2/resource/"  
        self._parse_dev_dict(dev_dict=dev_dict)
        self._HEADERS = {"hue-application-key":self._hue_key, "Content-Type":"application/json"}

    def _parse_dev_dict(self, dev_dict: Dict) -> None:
        """Parses device data and creates general, device agnostic, attributes"""
        self._dev_data = dev_dict
        self.name = self._dev_data["metadata"]["name"]
        self.id = dev_dict['id']
        self.dev_type = dev_dict['metadata']['archetype']

    def _get(self, url: str) -> Dict:
        """Retrievies Device(s) info"""
        req = requests.get(url=url, headers=self._HEADERS, verify=False)
        return json.loads(req.text)

    def _put(self, url: str, headers: Dict, body: Dict) -> None:
        """Modifies Device State"""
        req = requests.put(url=url, headers=headers, data=json.dumps(body), verify=False)


class HueLight(HueResource):
    ## TODO
    ## Implement light-specific functions such as on/off/brightness/colour etc.
    # def __init__(self, dev_dict: Dict, hue_hostname: str, hue_key: str) -> None:
        # super().__init__(dev_dict, hue_hostname, hue_key)

    def _parse_dev_dict(self, dev_dict: Dict) -> None:
        super()._parse_dev_dict(dev_dict) 
        self.url = self.base_url + f"/light/{self.id}"
        self.state = str(self._dev_data['on']['on'])
        # Smart plugs are categorised as lights, unfortunately
        if dev_dict['metadata']['archetype']!='plug':
            self.brightness_level = self._dev_data["dimming"]["brightness"]
            self.colour_temperature = self._dev_data["color_temperature"]["mirek"]



    ## TODO
    ## Lack of set "natural" light is a bit of an issue
    ## I have to check what time it is and trigger the adequate scene from 'natural light'
    ## Then on the other hand maybe it shouldn't be placed in the HueLight class but rather in the
    ## Room/Zone class? That way the HueLight class will be concise and limited to light-specific actions
    ## Such as on/off, brightness and colour temp? 
    ## Have to consider it and finally actually test dat shit
    ## Gotta also make another repo specifically for this project and not keep it in the "playground" project
    def turn_on(self) -> None:
        if self.state != 'true':
            body = {'on':{'on': True}}
            super()._put(self.url, self._HEADERS, body, verify=False)
            self.state = 'true'
    
    def turn_off(self) -> None:
        if self.state != 'false':
            body = {'on':{'on':False}}
            super()._put(self.url, self._HEADERS, body, verify=False)
            self.state = 'false'

    def change_brightness(self, b_level: int) -> None:
        if b_level > 100:
            level = 100
        elif b_level < 0:
            level = 0
        else:
            level = b_level
        body = {"dimming":{"brightness":level}}
        super()._put(self.url, self._HEADERS, body, verify=False)

    def change_temp(self, t_level: int) -> None:
        if t_level>500:
            level=500
        elif t_level<153:
            level=153
        else:
            level = t_level
        body = {"color_temperature":{"mirek":level}}
        super()._put(self.url, self._HEADERS, body, verify=False)


class HueRoom(HueResource):
        def __init__(self, dev_dict: Dict, hue_hostname: str, hue_key: str) -> None:
            super().__init__(dev_dict, hue_hostname, hue_key)
            self.state = self._get_state()
            self.scenes = {}

        def _parse_dev_dict(self, dev_dict: Dict) -> None:
            super()._parse_dev_dict(dev_dict)
            self.children = [child["rid"] for child in dev_dict['children']]
            self.url = self.base_url + f"/room/{self.id}"
            # ID allowing to controll all devices the room
            self.grouped_light_id = dev_dict["services"][0]["rid"]
            self.grouped_light_url = self.base_url + f"/grouped_light/{self.grouped_light_id}"

        def _get_state(self) -> str:
            req = super()._get(url=self.grouped_light_url)
            data = req["data"][0]
            return str(data["on"]["on"])

        def turn_on(self) -> None:
            if self.state != 'true':
                body = {'on':{'on':True}}
                super()._put(url=self.grouped_light_url, headers=self._HEADERS, body=body)
                self.state = 'true'

        def turn_off(self) -> None:
            if self.state != 'false':
                body = {'on':{'on':False}}
                super()._put(url=self.grouped_light_url, headers=self._HEADERS, body=body)
                self.state = 'false'

        def change_brightness(self, b_level: int) -> None:
            if b_level>100:
                level=100
            elif b_level < 0:
                level=0
            else:
                level = b_level
            body = {'dimming':{'brightness':level}}
            super()._put(url=self.grouped_light_url, headers=self._HEADERS, body=body)

        def set_scene(self, scene_name: str, brightness: int=None) -> None:
            if not brightness:
                body = {'recall':{'action':'active'}}
            else:
                if brightness > 100:
                    brightness=100
                elif brightness<1:
                    brightness=1
                body = {'recall':{'action':'active',
                                  'dimming':{'brightness':brightness}}}
            
            scene_url = self.base_url + f"scene/{self.scenes[scene_name.lower()]['id']}"
            super()._put(url=scene_url, headers=self._HEADERS, body=body)

class HueZone(HueResource):
    def __init__(self, dev_dict: Dict, hue_hostname: str, hue_key: str) -> None:
        super().__init__(dev_dict, hue_hostname, hue_key)
        self.state = self._get_state()
        self.scenes = {}

    def _parse_dev_dict(self, dev_dict: Dict) -> None:
        super()._parse_dev_dict(dev_dict)
        self.children = [child["rid"] for child in dev_dict['children']]
        self.grouped_light_id = dev_dict["services"][0]["rid"]
        self.url = self.base_url + f"/zone/{self.id}"
        self.grouped_light_id = dev_dict["services"][0]["rid"]
        self.grouped_light_url = self.base_url + f"/grouped_light/{self.grouped_light_id}"

    def _get_state(self) -> str:
        req = super()._get(self.grouped_light_url)
        data = req['data'][0]
        return str(data["on"]["on"])

    def turn_on(self) -> None:
        if self.state != 'true':
            body = {'on':{'on':True}}
            super()._put(self.grouped_light_url, self._HEADERS, body)
            self.state = 'true'

    def turn_off(self) -> None:
        if self.state != 'false':
            body = {'on':{'on':False}}
            super()._put(self.grouped_light_url, self._HEADERS, body)
            self.state = 'false'

    def change_brightness(self, b_level: int) -> None:
            if b_level>100:
                level=100
            elif b_level < 0:
                level=0
            else:
                level = b_level
            body = {'dimming':{'brightness':level}}
            super()._put(url=self.grouped_light_url, headers=self._HEADERS, body=body) 

    def set_scene(self, scene_name: str, brightness: int=None) -> None:
            if not brightness:
                body = {'recall':{'action':'active'}}
            else:
                if brightness > 100:
                    brightness=100
                elif brightness<1:
                    brightness=1
                body = {'recall':{'action':'active',
                                  'dimming':{'brightness':brightness}}}
            
            scene_url = self.base_url + f"scene/{self.scenes[scene_name.lower()]['id']}"
            super()._put(url=scene_url, headers=self._HEADERS, body=body)



class HueScene(HueResource):
    # def __init__(self, dev_dict: Dict, hue_hostname: str, hue_key: str) -> None:
    #     super().__init__(dev_dict, hue_hostname, hue_key)

    def _parse_dev_dict(self, dev_dict: Dict) -> None:
        super()._parse_dev_dict(dev_dict)
        self.children = [child['rid'] for child in dev_dict['children']]
        self.grouped_light_id = dev_dict["services"]["rid"]
        self.tg_area = dev_dict[""]