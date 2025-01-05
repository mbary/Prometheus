"""
This file contains the base class for all hue resources - HueResource
Alongside major devices such as: 

"""

## TODO Add stuff like __repr__, __str__ etc to create a pretty representatoin of the devices
from datetime import datetime
import json
import requests
from typing import Dict, Optional, Union
from dataclasses import dataclass
from pprint import pprint
import warnings
warnings.filterwarnings('ignore')

from .exceptions import HueConnectionError, HueResponseError, HueValidationError

class HueResource:
    """Base class representing a Philips Hue resource.

    This class serves as a foundation for all Hue ecosystem devices and resources.
    It provides common attributes and methods shared across different Hue devices.

    Parameters
    ----------
    dev_dict : Dict
        Dictionary containing device information and configuration
    hue_hostname : str
        Hostname/IP address of the Hue bridge
    hue_key : str
        Authentication key for the Hue bridge API

    Attributes
    ----------
    name : str
        Name of the device (lowercase)
    id : str
        Unique identifier of the device
    dev_type : str
        Device archetype/type
    base_url : str
        Base URL for API requests
    _dev_data : Dict
        Raw device data dictionary
    _hue_hostname : str
        Stored Hue bridge hostname
    _hue_key : str
        Stored Hue bridge authentication key
    _HEADERS : Dict
        HTTP headers used for API requests

    Methods
    -------
    _parse_dev_dict(dev_dict)
        Parses device dictionary to set common attributes
    _get(url)
        Makes GET request to retrieve device information
    _put(url, headers, body)
        Makes PUT request to modify device state

    Notes
    -----
    This is a base class meant to be inherited by specific device type classes
    like lights, switches, zones, rooms etc.
    """
    ## TODO
    ## This is meant to be a Hue resource base class.
    ## It should have all attributes/capabilites shared across the HUE ecosystem
    ## Attrs: rid, rtype, product data etc.
    ## methods such as get/put etc
    ## in innit, there should be a func that automatically parses a dictionary


    ## based on this, using inheritence, we can create subclasses such as lights, switches, zones, rooms etc.
    ## They will be extended by device-specific functionalities such as on/off and whatever the fuck else I manage to find
    def __init__(self, 
                 dev_dict:Dict, 
                 hue_hostname: str, 
                 hue_key: str,
                 http_client: Optional[requests.Session] = None) -> None:
        
        # Check Resource Input is valid
        if not all(field in dev_dict for field in ['id','metadata']):
            raise HueValidationError(f"Invalid Resource. Missing required fields: 'id' or 'metadata'")
        
        self._http_client = http_client or requests.Session()
        self._hue_hostname = hue_hostname 
        self._hue_key = hue_key
        self.base_url = f"https://{self._hue_hostname}/clip/v2/resource/"  
        self._HEADERS = {
            "hue-application-key":self._hue_key,
              "Content-Type":"application/json"
              }
        
        self._parse_dev_dict(dev_dict=dev_dict)

    def _parse_dev_dict(self, dev_dict: Dict) -> None:
        """Parses device data and creates general, device agnostic, attributes"""
        self._dev_data = dev_dict
        self.name = self._dev_data["metadata"]["name"].lower()
        self.id = dev_dict['id']
        self.dev_type = dev_dict['metadata']['archetype']

    def _get(self, url: str) -> Dict:
        """Retrievies Device(s) info"""
        try:
            response = self._http_client.get(url=url, headers=self._HEADERS, verify=False)
            response.raise_for_status()
            return response.json()
        # req = requests.get(url=url, headers=self._HEADERS, verify=False)
        # return json.loads(req.text)
        except requests.exceptions.RequestException as e:
            raise HueConnectionError(f"Failed to connect to Hue Bridge: {str(e)}")
        except ValueError as e:
            raise HueResponseError(f"Failed to parse response from Hue Bridge: {str(e)}")

    def _put(self, url: str, headers: Dict, body: Dict) -> None:
        """Modifies Device State"""
        if not body:
            raise HueValidationError("PUT request requires a body")
        try:
            json_data = json.dumps(body)
            response = self._http_client.put(url=url, headers=headers, data=json_data, verify=False)
            response.raise_for_status()

            if response.text:
                # if 'errors' in response.json():
                if len(response.json()['errors']):
                    raise HueResponseError(f"Failed to update device state: {response.json()['errors']}")
                
        # req = requests.put(url=url, headers=headers, data=json.dumps(body), verify=False)

        except json.JSONDecodeError as e:
            raise HueResponseError(f"Invalid request body: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise HueConnectionError(f"Failed to connect to Hue Bridge: {e}")
        except ValueError as e:
            raise HueResponseError(f"Failed to parse response from Hue Bridge: {str(e)}")
        

@dataclass
class LightState:
    """ Represents the state of a Hue Light """

    is_on: bool
    brightness: Optional[int] = None
    colour_temp: Optional[int] = None
    reachable: bool = True
    last_updated: datetime = datetime.now()


class HueLight(HueResource):
    """A class representing a Philips Hue light device.
    This class extends HueResource to provide specific functionality for Hue lights,
    including controlling power state, brightness, and color temperature. It handles both
    regular lights and smart plugs (which are categorized as lights in the Hue system).
    Parameters
    ----------
    dev_dict : Dict
        Dictionary containing the device information from the Hue Bridge
    hue_hostname : str
        Hostname or IP address of the Hue Bridge
    hue_key : str
        Authentication key for the Hue Bridge API
    Attributes
    ----------
    url : str
        The complete API URL for this specific light
    state : str
        Current power state of the light ('true' or 'false')
    brightness_level : float
        Current brightness level (0-100), only for actual lights
    colour_temperature : int
        Current color temperature in mirek (153-500), only for actual lights
    Methods
    -------
    turn_on()
        Turns the light on if it's not already on
    turn_off()
        Turns the light off if it's not already off
    change_brightness(b_level: int)
        Changes the brightness level (0-100)
    change_temp(t_level: int)
        Changes the color temperature (153-500 mirek)
    Notes
    -----
    Smart plugs are handled differently from regular lights - they only support on/off
    functionality and don't have brightness or color temperature attributes.
    """

    MIN_BRIGHTNESS = 0
    MAX_BRIGHTNESS = 100
    MIN_COLOR_TEMP = 153  # Warmest - 2000K
    MAX_COLOR_TEMP = 500  # Coolest - 6500K

    def __init__(
        self, 
        dev_dict: Dict, 
        hue_hostname: str, 
        hue_key: str ) -> None:
        super().__init__(dev_dict, hue_hostname, hue_key)
        self._current_state = self._initialise_state()


    def _parse_dev_dict(self, dev_dict: Dict) -> None:
        try:
            super()._parse_dev_dict(dev_dict) 
            self.url = self.base_url + f"/light/{self.id}"
            self.state = str(self._dev_data['on']['on'])
            self._is_plug = dev_dict['metadata']['archetype']=='plug'
            # Smart plugs are categorised as lights, unfortunately
            if not self._is_plug:
                if 'dimming' not in self._dev_data.keys() or 'color_temperature' not in self._dev_data.keys():
                    raise HueValidationError("Invalid light device data")
                
                self.brightness_level = self._dev_data["dimming"]["brightness"]
                self.colour_temperature = self._dev_data["color_temperature"]["mirek"]
        except KeyError as e:
            raise HueValidationError(f"Invalid light device data: {str(e)}")
        
    def _initialise_state(self) -> LightState:

        try:
            response = self._get(self.url)
            data = response['data'][0]

            return LightState(
                is_on = data['on']['on'],
                brightness = data['dimming']['brightness'] if not self._is_plug else None,
                colour_temp = data['color_temperature']['mirek'] if not self._is_plug else None,
                reachable = True,
                last_updated=datetime.now()
            )
        
        except Exception as e:
            raise e

    def turn_on(self) -> None:
        if self.state != 'true':
            body = {'on':{'on': True}}
            super()._put(self.url, self._HEADERS, body, verify=False)
            self.state = 'true'
            self._current_state.is_on = True
            self._current_state.last_updated = datetime.now()
    
    def turn_off(self) -> None:
        if self.state != 'false':
            body = {'on':{'on':False}}
            super()._put(self.url, self._HEADERS, body, verify=False)
            self.state = 'false'
            self._current_state.is_on = False
            self._current_state.last_updated = datetime.now()

    def change_brightness(self, b_level: int) -> None:

        level = max(self.MIN_BRIGHTNESS, min(b_level, self.MAX_BRIGHTNESS))
        body = {"dimming":{"brightness":level}}
        super()._put(self.url, self._HEADERS, body, verify=False)
        self._current_state.brightness=level
        self._current_state.last_updated = datetime.now()

    def change_temp(self, t_level: int) -> None:

        level = max(self.MIN_COLOR_TEMP, min(t_level, self.MAX_COLOR_TEMP))
        body = {"color_temperature":{"mirek":level}}
        super()._put(self.url, self._HEADERS, body, verify=False)


class HueRoom(HueResource):
        """A class representing a Philips Hue room with its associated controls and states.
        This class inherits from HueResource and provides functionality to control Philips Hue
        rooms, including turning lights on/off, changing brightness, and setting scenes.
        Parameters
        ----------
        dev_dict : Dict
            Dictionary containing the room device information from Hue Bridge
        hue_hostname : str
            Hostname or IP address of the Hue Bridge
        hue_key : str
            Authentication key for the Hue Bridge API
        Attributes
        ----------
        state : str
            Current state of the room ('true' for on, 'false' for off)
        scenes : dict
            Dictionary of available scenes for the room
        children : list
            List of child device IDs in the room
        url : str
            API endpoint URL for this room
        grouped_light_id : str
            ID for controlling all lights in the room as a group
        grouped_light_url : str
            API endpoint URL for controlling grouped lights
        Methods
        -------
        turn_on()
            Turns on all lights in the room. For office and bedroom, sets 'natural light' scene
        turn_off()
            Turns off all lights in the room
        change_brightness(b_level: int)
            Changes brightness level of all lights in the room
        set_scene(scene_name: str, brightness: int=None)
            Activates a specific scene in the room with optional brightness setting
        Notes
        -----
        The brightness levels are always normalized between 0 and 100.
        Scene names are case-insensitive.
        """
        def __init__(self, dev_dict: Dict, hue_hostname: str, hue_key: str) -> None:
            super().__init__(dev_dict, hue_hostname, hue_key)
            self.state = self._get_state()
            self.scenes = {}

        def _parse_dev_dict(self, dev_dict: Dict) -> None:

            try:
                super()._parse_dev_dict(dev_dict)

                if 'children' not in dev_dict:
                    raise HueValidationError(f"{self.name} room appears to be empty.\nAdd devices for full experience") 

                self.children = [child["rid"] for child in dev_dict['children']]
                self.url = self.base_url + f"/room/{self.id}"

                # ID allowing to controll all devices the room
                if not dev_dict["services"][0]["rid"]:
                    raise HueValidationError(f"Missing grouped light ID for {self.name} room")
                self.grouped_light_id = dev_dict["services"][0]["rid"]
                self.grouped_light_url = self.base_url + f"/grouped_light/{self.grouped_light_id}"

            except KeyError as e:
                raise HueValidationError(f"Invalid room data: {str(e)}")
            except Exception as e:
                raise HueValidationError(f"Failed to parse room data: {str(e)}")
                
        def _get_state(self) -> str:
            try:
                response = super()._get(self.grouped_light_url)

                if not response["data"]:
                    raise HueResponseError(f"Failed to retrieve state for {self.name} room")
                data = response["data"][0]

                if 'on' not in data:
                    raise HueResponseError(f"Failed to retrieve state for {self.name} room")
                
                return str(data["on"]["on"])
            
            except HueResponseError:
                raise
            except Exception as e:
                raise HueConnectionError(f"Failed to retrieve state for {self.name} room: {str(e)}")

        def turn_on(self) -> None:
            if self.state != 'true':
                try:
                    if self.name == 'office' or self.name == 'bedroom':
                        self.set_smart_scene(scene_name='natural light')
                        self.state = 'true'
                    else:
                        body = {'on':{'on':True}}
                        super()._put(url=self.grouped_light_url, headers=self._HEADERS, body=body)
                        self.state = 'true'
                except Exception as e:
                    raise HueConnectionError(f"Failed to turn on {self.name} room: {str(e)}")
                
        def turn_off(self) -> None:
            if self.state != 'false':
                try:
                    body = {'on':{'on':False}}
                    super()._put(url=self.grouped_light_url, headers=self._HEADERS, body=body)
                    self.state = 'false'
                except Exception as e:
                    raise HueConnectionError(f"Failed to turn off {self.name} room: {str(e)}")
                
        def change_brightness(self, b_level: int) -> None:
            
            try:
                if not isinstance(b_level, (int, float)):
                        raise HueValidationError("Brightness level must be a number")   
                
                normalised_brightness = max(1, min(b_level, 100))
                
                body = {'dimming':{'brightness':normalised_brightness}}
                super()._put(url=self.grouped_light_url, headers=self._HEADERS, body=body)

            except HueValidationError:
                raise
            except Exception as e:
                raise HueConnectionError(f"Failed to change brightness in {self.name} room: {str(e)}")
            
        def set_scene(self, scene_name: str, brightness: int=None) -> None:
            try:
                scene_name = scene_name.lower()
                if scene_name not in self.scenes:
                    raise HueValidationError(f"Scene '{scene_name}' not found in {self.name} room")
                
                if not brightness:
                    body = {'recall':{'action':'active'}}
                else:
                    if not isinstance(brightness, (int, float)):
                        raise HueValidationError("Brightness level must be a number")   
                    normalised_brightness = max(1, min(brightness, 100))
                    body = {'recall':{'action':'active',
                                    'dimming':{'brightness':normalised_brightness}}}

                
                scene_url = self.base_url + f"scene/{self.scenes[scene_name]['id']}"
                super()._put(url=scene_url, headers=self._HEADERS, body=body)
                self.state = 'true'

            except HueValidationError:
                raise
            except Exception as e:
                raise HueConnectionError(f"Failed to set scene: {scene_name} in {self.name} room: {str(e)}")

        def set_smart_scene(self, scene_name: str, brightness: int=None) -> None:
            try:
                scene_name = scene_name.lower()
                if scene_name not in self.scenes:
                    raise HueValidationError(f"Scene '{scene_name}' not found in {self.name} room")
                
                if not brightness:
                    body = {'recall':{'action':'activate'}}
                else:
                    if not isinstance(brightness, (int, float)):
                        raise HueValidationError("Brightness level must be a number")   
                    normalised_brightness = max(1, min(brightness, 100))
                    body = {'recall':{'action':'activate',
                                    'dimming':{'brightness':normalised_brightness}}}
                
                scene_url = self.base_url + f"smart_scene/{self.scenes[scene_name.lower()]['id']}"
                super()._put(url=scene_url, headers=self._HEADERS, body=body)
        
            except HueValidationError:
                raise
            except Exception as e:
                raise HueConnectionError(f"Failed to set smart scene: {scene_name} in {self.name} room: {str(e)}")
        


class HueZone(HueResource):
    """A class representing a Philips Hue Zone.
    This class provides functionality to control a group of Philips Hue lights that are organized
    into a zone. It allows for basic operations like turning the lights on/off, changing brightness,
    and setting scenes.
    Parameters
    ----------
    dev_dict : Dict
        Dictionary containing device information from the Hue Bridge
    hue_hostname : str
        Hostname or IP address of the Hue Bridge
    hue_key : str
        Authentication key for the Hue Bridge API
    Attributes
    ----------
    state : str
        Current state of the zone ('true' for on, 'false' for off)
    scenes : dict
        Dictionary of available scenes for this zone
    children : list
        List of child device IDs in this zone
    grouped_light_id : str
        ID of the grouped light service
    url : str
        API endpoint URL for this zone
    grouped_light_url : str
        API endpoint URL for the grouped light service
    Methods
    -------
    turn_on()
        Turns on all lights in the zone. For office and bedroom zones, 
        sets the 'natural light' scene
    turn_off()
        Turns off all lights in the zone
    change_brightness(b_level: int)
        Changes the brightness level of the zone
    set_scene(scene_name: str, brightness: int = None)
        Activates a specific scene in the zone with optional brightness level
    Notes
    -----
    This class inherits from HueResource and implements specific functionality
    for controlling Philips Hue zones through the Hue Bridge API v2.
    """
    def __init__(self, dev_dict: Dict, hue_hostname: str, hue_key: str) -> None:
        super().__init__(dev_dict, hue_hostname, hue_key)
        self.state = self._get_state()
        self.scenes = {}

    def _parse_dev_dict(self, dev_dict: Dict) -> None:
        try:
            super()._parse_dev_dict(dev_dict)

            if 'children' not in dev_dict:
                raise HueValidationError(f"{self.name} zone appears to be empty.\nAdd devices for full experience")
            
            self.children = [child["rid"] for child in dev_dict['children']]
            self.url = self.base_url + f"/zone/{self.id}"
            self.grouped_light_id = dev_dict["services"][0]["rid"]
            self.grouped_light_url = self.base_url + f"/grouped_light/{self.grouped_light_id}"

        except KeyError as e:
            raise HueValidationError(f"Invalid zone data: {str(e)}")
        except Exception as e:
            raise HueValidationError(f"Failed to parse zone data: {str(e)}")

    def _get_state(self) -> str:
        try:
            response = super()._get(self.grouped_light_url)

            if not response["data"]:
                raise HueResponseError(f"Failed to retrieve state for {self.name} zone")
            data = response["data"][0]

            return str(data["on"]["on"])
        
        except HueResponseError:
            raise
        except Exception as e:
            raise HueConnectionError(f"Failed to retrieve state for {self.name} zone: {str(e)}")


    def turn_on(self) -> None:
        if self.state != 'true':
            try:
                if self.name == 'office' or self.name == 'bedroom':
                    self.set_smart_scene(scene_name='natural light')
                    self.state = 'true'
                else:
                    body = {'on':{'on':True}}
                    super()._put(url=self.grouped_light_url, headers=self._HEADERS, body=body)
                    self.state = 'true'
            except Exception as e:
                raise HueConnectionError(f"Failed to turn on {self.name} zone: {str(e)}")
            
    def turn_off(self) -> None:
        if self.state != 'false':
            try:
                
                body = {'on':{'on':False}}
                super()._put(self.grouped_light_url, self._HEADERS, body)
                self.state = 'false'
            except Exception as e:
                raise HueConnectionError(f"Failed to turn off {self.name} zone: {str(e)}")
            
    def change_brightness(self, b_level: int) -> None:
            
            try:
                if not isinstance(b_level, (int, float)):
                        raise HueValidationError("Brightness level must be a number")   
                
                normalised_brightness = max(1, min(b_level, 100))
                body = {'dimming':{'brightness':normalised_brightness}}
                super()._put(url=self.grouped_light_url, headers=self._HEADERS, body=body)

            except HueValidationError:
                raise
            except Exception as e:
                raise HueConnectionError(f"Failed to change brightness in {self.name} zone: {str(e)}")

    def set_scene(self, scene_name: str, brightness: int=None) -> None:
            try:
                scene_name = scene_name.lower()
                if scene_name not in self.scenes:
                    raise HueValidationError(f"Scene '{scene_name}' not found in {self.name} zone")
                
                if not brightness:
                    body = {'recall':{'action':'active'}}
                else:
                    if not isinstance(brightness, (int, float)):
                        raise HueValidationError("Brightness level must be a number")   
                    normalised_brightness = max(1, min(brightness, 100))
                    body = {'recall':{'action':'active',
                                    'dimming':{'brightness':normalised_brightness}}}

                
                scene_url = self.base_url + f"scene/{self.scenes[scene_name]['id']}"
                super()._put(url=scene_url, headers=self._HEADERS, body=body)
                self.state = 'true'
                
            except HueValidationError:
                raise
            except Exception as e:
                raise HueConnectionError(f"Failed to set scene: {scene_name} in {self.name} zone: {str(e)}")

    def set_smart_scene(self, scene_name: str, brightness: int=None) -> None:
            try:
                scene_name = scene_name.lower()
                if scene_name not in self.scenes:
                    raise HueValidationError(f"Scene '{scene_name}' not found in {self.name} zone")
                
                if not brightness:
                    body = {'recall':{'action':'activate'}}
                else:
                    if not isinstance(brightness, (int, float)):
                        raise HueValidationError("Brightness level must be a number")   
                    normalised_brightness = max(1, min(brightness, 100))
                    body = {'recall':{'action':'activate',
                                    'dimming':{'brightness':normalised_brightness}}}
                
                scene_url = self.base_url + f"smart_scene/{self.scenes[scene_name.lower()]['id']}"
                super()._put(url=scene_url, headers=self._HEADERS, body=body)
        
            except HueValidationError:
                raise
            except Exception as e:
                raise HueConnectionError(f"Failed to set smart scene: {scene_name} in {self.name} zone: {str(e)}")
    