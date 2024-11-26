"""
This file contains the base class for all hue resources - HueResource
Alongside major devices such as: 

"""

import json
import requests
from typing import Dict


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
        self._parse_dev_dict(dev_dict=dev_dict)
        self._hue_hostname = hue_hostname ## TODO remove hostaname, this should be kept in the bridge class
        self._hue_key = hue_key
        self.base_url = f"https://{self._hue_hostname}/clip/v2/resource/" ## TODO remove, this should be kept in the bridge class
        self._headers = self._build_headers() ## TODO remove, this should be kept in the bridge class



    def _parse_dev_dict(self, dev_dict: Dict) -> None:
        """Parses device data and creates general, device agnostic, attributes"""
        self._dev_data = dev_dict["data"]
        self.product_name = self._dev_data["product_data"]["product_name"]
        self.resource_name = self._dev_data["metadata"]["name"]
        self._services = {adict["rtype"]:adict["rid"] for adict in self._dev_data["services"]}
        self.id = dev_dict['id']

    def _build_headers(self):
        headers = {
            'hue-application-key':self._hue_key,
            'Content-Type':'application/json'
        }
        return headers
    
    def _get(self, url: str) -> Dict:
        """Retrievies Device(s) info"""
        req = requests.get(url=url, headers=self._headers, verify=False)
        return json.loads(req.text)
    
    def _put(self, url: str, headers: Dict, body: Dict) -> None:
        """Modifies Device State"""
        req = requests.put(url=url, headers=headers, data=json.dumps(body), verify=False)


