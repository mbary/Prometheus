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
    http_client : Optional[requests.Session]
        Custom HTTP client session, defaults to new requests.Session()

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
    _http_client : requests.Session
        HTTP client for making requests

    Methods
    -------
    _parse_dev_dict(dev_dict)
        Parses device dictionary to set common attributes
    _get(url)
        Makes GET request to retrieve device information
    _put(url, headers, body)
        Makes PUT request to modify device state

    Raises
    ------
    HueValidationError
        When required fields are missing in dev_dict
        When PUT request body is empty
    HueConnectionError
        When connection to Hue Bridge fails
    HueResponseError
        When response parsing fails
        When Hue Bridge returns errors
        When request body is invalid JSON
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
        """Parses device dictionary and sets basic device attributes.

        Args:
            dev_dict (Dict): Dictionary containing device information with required keys:
                - id: Device identifier
                - metadata: Dict containing:
                    - name: Device name
                    - archetype: Device type/archetype

        Sets the following instance attributes:
            - _dev_data: Raw device data dictionary
            - name: Lowercase device name
            - id: Device identifier
            - dev_type: Device archetype
        """
        self._dev_data = dev_dict
        self.name = self._dev_data["metadata"]["name"].lower()
        self.id = dev_dict['id']
        self.dev_type = dev_dict['metadata']['archetype']

    def _get(self, url: str) -> Dict:
        """Makes a GET request to the specified URL using the configured HTTP client.

        Args:
            url (str): The URL to send the GET request to.

        Returns:
            Dict: The JSON response from the server parsed into a dictionary.

        Raises:
            HueConnectionError: If there is an error connecting to the Hue Bridge.
            HueResponseError: If the response from the Hue Bridge cannot be parsed.
        """
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
        """Perform a PUT request to the Hue Bridge.
        This method sends a PUT request with JSON data to the specified URL on the Hue Bridge.
        Args:
            url (str): The endpoint URL to send the PUT request to
            headers (Dict): Headers to include in the request
            body (Dict): JSON-serializable dictionary containing the request body
        Raises:
            HueValidationError: If the request body is empty
            HueResponseError: If the response contains errors or cannot be parsed
            HueConnectionError: If connection to the Hue Bridge fails
        Returns:
            None
        """
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
    Raises
    ------
    HueValidationError
        If the device dictionary is missing required fields or contains invalid data
        for lights (dimming and color_temperature fields)
    KeyError
        If required keys are missing in the device dictionary during parsing
    Exception
        If there are communication errors with the Hue Bridge or response processing fails
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
        """Parse device dictionary data and update instance attributes.
        This method processes the device data dictionary received from the Hue API to update
        the light device's attributes. It handles both regular lights and smart plugs,
        which are categorized as lights in the Hue system.
        Args:
            dev_dict (Dict): Dictionary containing device data from Hue API
        Raises:
            HueValidationError: If the device data is invalid or missing required fields
                for lights (dimming and color_temperature)
        Notes:
            - For regular lights, both dimming and color_temperature must be present
            - Smart plugs are identified by their 'plug' archetype in metadata
            - Updates url, state, brightness_level, and colour_temperature attributes
        """
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
        """
        Initializes the state of the Hue device by fetching current data from the Philips Hue Bridge.
        Returns:
            LightState: Object containing the current state of the device including:
                - on/off status
                - brightness level (None for plug devices)
                - color temperature in mirek (None for plug devices)
                - reachability status
                - last update timestamp
        Raises:
            Exception: If there is an error communicating with the Hue Bridge or processing the response
        """

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
        """Turns on the device by sending an HTTP PUT request.

        The method checks if the device is not already on ('true' state) before sending
        the request. If the device is already on, no action is taken.

        Note: Current implementation has a limitation where state checking prevents
        overriding active scenes. This may need refactoring to allow direct state
        changes regardless of current state.

        Side Effects:
            - Updates device state to 'true'
            - Updates internal _current_state object:
                - Sets is_on to True
                - Updates last_updated timestamp

        Returns:
            None
        """
        if self.state != 'true': ##TODO This shit has to be changed. it's bloody annoying. if I remove it, then I can over-ride current state regardless of whatit is
                                 ##     Meaning e.g. if A scene is active but I want to set it to e.g. natural light in bedroom/office then I can just say "turn on office" instead of "set smart_scene in office"
            body = {'on':{'on': True}}
            super()._put(self.url, self._HEADERS, body)
            self.state = 'true'
            self._current_state.is_on = True
            self._current_state.last_updated = datetime.now()
    
    def turn_off(self) -> None:
        """
        Turns off the device by sending a PUT request to turn off the light.

        The method updates the device state to 'false' and updates the current state
        object with the new status and timestamp only if the device is currently on.

        Returns:
            None
        """
        if self.state != 'false':
            body = {'on':{'on':False}}
            super()._put(self.url, self._HEADERS, body)
            self.state = 'false'
            self._current_state.is_on = False
            self._current_state.last_updated = datetime.now()

    def change_brightness(self, b_level: int) -> None:
        """Changes the brightness level of the device.

        Args:
            b_level (int): The target brightness level to set. Will be clamped between
                MIN_BRIGHTNESS and MAX_BRIGHTNESS.

        Returns:
            None

        Notes:
            Updates the device's current state and timestamp after changing brightness.
            The brightness value is sent via PUT request to the device URL.
        """

        level = max(self.MIN_BRIGHTNESS, min(b_level, self.MAX_BRIGHTNESS))
        body = {"dimming":{"brightness":level}}
        super()._put(self.url, self._HEADERS, body)
        self._current_state.brightness=level
        self._current_state.last_updated = datetime.now()

    def change_temp(self, t_level: int) -> None:
        """Changes the color temperature of the device.

        Sets color temperature within device's allowed range. The value is automatically capped
        between MIN_COLOR_TEMP and MAX_COLOR_TEMP if outside these bounds.

        Args:
            t_level (int): Target color temperature in mirek (higher values = warmer colors,
                lower values = cooler colors)

        Returns:
            None

        Note:
            Mirek is reciprocal megakelvin (MK^-1). Converting from Kelvin to mirek:
            mirek = 1,000,000 / color_temperature_in_kelvin
        """

        level = max(self.MIN_COLOR_TEMP, min(t_level, self.MAX_COLOR_TEMP))
        body = {"color_temperature":{"mirek":level}}
        super()._put(self.url, self._HEADERS, body)


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
        devices : dict  
            Dictionary mapping light names to HueLight objects for devices in this room
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
        set_smart_scene(scene_name: str, brightness: int=None)
            Activates a smart scene in the room with optional brightness setting
        Raises
        ------
        HueValidationError
            When room data is invalid:
            - Empty room with no devices
            - Missing grouped light ID
            - Invalid scene name
            - Invalid brightness value type
        HueConnectionError  
            When there are connection/communication errors with Hue Bridge:
            - Failed API requests
            - Failed state retrieval
            - Failed to turn lights on/off
            - Failed to change brightness
            - Failed to set scenes
        HueResponseError
            When API response data is invalid:
            - Empty response data
            - Missing state information
        Notes
        -----
        The brightness levels are always normalized between 0 and 100.
        Scene names are case-insensitive.
        """
        def __init__(self, dev_dict: Dict, hue_hostname: str, hue_key: str) -> None:
            super().__init__(dev_dict, hue_hostname, hue_key)
            self.state = self._get_state()
            self.scenes = {}
            self.devices = {}

        def _parse_dev_dict(self, dev_dict: Dict) -> None:
            """
            Parse room device dictionary and set instance attributes.

            This method processes a dictionary containing room device data from the Hue Bridge API,
            extending the base device parsing with room-specific attributes.

            Args:
                dev_dict (Dict): Dictionary containing room device data from Hue Bridge

            Raises:
                HueValidationError: If required room data is missing or invalid:
                    - When room has no children devices
                    - When grouped light ID is missing
                KeyError: If expected dictionary keys are not found
                Exception: For other parsing errors

            Sets the following attributes:
                children (List[str]): List of child device IDs in the room
                url (str): API endpoint URL for this room
                grouped_light_id (str): ID for controlling all lights in the room as a group
                grouped_light_url (str): API endpoint URL for the grouped light control
            """

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
            """
            Retrieves the current state (on/off) of the grouped light.
            Returns:
                str: String representation of the light state ('True' for on, 'False' for off)
            Raises:
                HueResponseError: If the response data is empty or doesn't contain 'on' status
                HueConnectionError: If there is any other error during the API request
            """
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
            """
            Turns on the lights in a room.

            For 'office' and 'bedroom', sets the 'natural light' scene.
            For other rooms, simply turns on the lights.

            The method updates the internal state to 'true' once successful.

            Raises:
                HueConnectionError: If there's an error communicating with the Hue Bridge 
                                   or turning on the lights.
            """
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
            """
            Turn off the lights in this room.

            Attempts to set the room's lights to OFF state if they are currently ON.
            Makes a PUT request to the Philips Hue Bridge API.

            Raises:
                HueConnectionError: If there is an error communicating with the Hue Bridge
                    while attempting to turn off the lights.

            Example:
                >>> room.turn_off()
            """
            if self.state != 'false':
                try:
                    body = {'on':{'on':False}}
                    super()._put(url=self.grouped_light_url, headers=self._HEADERS, body=body)
                    self.state = 'false'
                except Exception as e:
                    raise HueConnectionError(f"Failed to turn off {self.name} room: {str(e)}")
                
        def change_brightness(self, b_level: int) -> None:
            """
            Change brightness level of a Hue room lights.
            Args:
                b_level (int): Brightness level to set (1-100).
                    Values outside this range will be normalized to fit within it.
            Raises:
                HueValidationError: If brightness level is not a number.
                HueConnectionError: If there is an error communicating with the Hue bridge.
            Notes:
                The brightness level is automatically normalized to fall within 1-100 range
                if values outside this range are provided.
            """
            
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
            """Sets a scene for the Hue room.
            This method activates a predefined scene in the Hue room, optionally with a specified brightness level.
            Args:
                scene_name (str): Name of the scene to activate. Must exist in the room's scenes.
                brightness (int, optional): Brightness level between 1-100. If not provided, scene's default brightness is used.
            Raises:
                HueValidationError: If scene name doesn't exist or brightness value is invalid.
                HueConnectionError: If there's a connection error while setting the scene.
            Returns:
                None
            """
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
            """Set a smart scene for the room with optional brightness level.
            This method activates a predefined smart scene in the room. The scene must exist
            in the room's available scenes. Optionally, a brightness level can be specified.
            Args:
                scene_name (str): Name of the scene to activate. Case-insensitive.
                brightness (int, optional): Brightness level between 1-100. If not provided,
                    the scene's default brightness will be used.
            Raises:
                HueValidationError: If the scene name is not found or brightness is invalid.
                HueConnectionError: If there's an error connecting to the Hue Bridge.
            Returns:
                None
            """
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
    devices : dict
        Dictionary mapping light names to HueLight objects for devices in this zone
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
    set_smart_scene(scene_name: str, brightness: int = None)
        Sets a smart scene for the zone with optional brightness
    Raises
    ------
    HueValidationError
        When required data is missing/invalid, scene doesn't exist, or brightness is invalid
        When there are issues communicating with the Hue Bridge
    HueResponseError
        When the API response is invalid or state retrieval fails
    Notes
    -----
    This class inherits from HueResource and implements specific functionality
    for controlling Philips Hue zones through the Hue Bridge API v2.
    """
    def __init__(self, dev_dict: Dict, hue_hostname: str, hue_key: str) -> None:
        super().__init__(dev_dict, hue_hostname, hue_key)
        self.state = self._get_state()
        self.scenes = {}
        self.devices = {}

    def _parse_dev_dict(self, dev_dict: Dict) -> None:
        """
        Parse the device dictionary for zone-specific attributes.
        This method extends the base class parsing functionality by extracting zone-specific
        data like children devices, URLs and grouped light information.
        Args:
            dev_dict (Dict): Dictionary containing zone device data from Hue Bridge
        Raises:
            HueValidationError: If the zone is empty (no children) or if required data is missing/invalid
        Returns:
            None
        Note:
            This method assumes the existence of 'children' and 'services' keys in the device dictionary
            for proper zone configuration.
        """
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
        """
        Retrieves the current state (on/off) of the zone.
        Returns:
            str: String representation of the zone state ('True' for on, 'False' for off)
        Raises:
            HueResponseError: If the API response is invalid or state retrieval fails
            HueConnectionError: If there is a connection or general error while retrieving the state
        """
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
        """Turns on the lights in the zone.

        For 'office' and 'bedroom' zones, it sets the 'natural light' scene.
        For other zones, it simply turns on the lights.

        Raises
        ------
        HueConnectionError
            If there is an error communicating with the Hue Bridge while attempting to turn on the zone.
        """
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
        """
        Turns off the lights in this zone.

        The method changes the state of the lights to off if they are currently on.
        It sends a PUT request to the Hue Bridge with the 'on' state set to False.

        Raises
        ------
        HueConnectionError
            If there is an error communicating with the Hue Bridge while attempting to turn off the lights.
        """
        if self.state != 'false':
            try:
                body = {'on':{'on':False}}
                super()._put(self.grouped_light_url, self._HEADERS, body)
                self.state = 'false'
            except Exception as e:
                raise HueConnectionError(f"Failed to turn off {self.name} zone: {str(e)}")
            
    def change_brightness(self, b_level: int) -> None:
            """Changes the brightness level of the Hue zone/room.

            Args:
                b_level (int): Brightness level between 1-100. Values outside this range will be normalized.

            Raises:
                HueValidationError: If brightness level is not a number.
                HueConnectionError: If there is an error communicating with the Hue Bridge.

            Returns:
                None
            """
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
            """
            Activates a specific scene for the Hue device/zone with optional brightness setting.
            Args:
                scene_name (str): Name of the scene to be activated. Must exist in the device's scenes.
                brightness (int, optional): Brightness level between 1-100. If not provided, 
                    scene's default brightness is used. Defaults to None.
            Raises:
                HueValidationError: When scene_name doesn't exist or brightness is not a number.
                HueConnectionError: When API request fails due to connection or other errors.
            Returns:
                None
            """
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
            """Sets a smart scene for the Hue device.
            This method activates a smart scene with an optional brightness setting. The scene must exist
            in the device's available scenes.
            Args:
                scene_name (str): The name of the scene to activate (case-insensitive).
                brightness (int, optional): Brightness level between 1-100. If not provided, 
                    scene will be activated with default brightness.
            Raises:
                HueValidationError: If the scene name is not found or brightness is invalid.
                HueConnectionError: If there's an error communicating with the Hue bridge.
            Returns:
                None
            """
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
    