import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from ..device import HueLight, HueResource
from ..exceptions import HueConnectionError, HueValidationError, HueResponseError

@pytest.fixture
def valid_light_dict():
    return {
        "id": "test_light_1",
        "metadata": {
            "name": "Test Light",
            "archetype": "sultanbulb"  # Not a plug
        },
        "on": {
            "on": 'true'
        },
        "dimming": {
            "brightness": 50.0
        },
        "color_temperature": {
            "mirek": 300
        }
    }

@pytest.fixture
def valid_plug_dict():
    return {
        "id": "test_plug_1",
        "metadata": {
            "name": "Test Plug",
            "archetype": "plug"
        },
        "on": {
            "on": 'false'
        }
    }

@pytest.fixture
def mock_responses():
    """Fixture providing common mock responses for API calls"""
    return {
        "get_light_state": {
            "data": [{
                "on": {"on": True},
                "dimming": {"brightness": 50.0},
                "color_temperature": {"mirek": 300}
            }]
        }
    }

class TestHueLight:
    """Test suite for HueLight class"""

    def test_initialize_regular_light(self, valid_light_dict):
        """Test initialization of a regular light with valid data"""
        # Mock the _get method to return a valid state
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = {
                "data": [{
                    "on": {"on": True},
                    "dimming": {"brightness": 50.0},
                    "color_temperature": {"mirek": 300}
                }]
            }
            
            light = HueLight(valid_light_dict, "test_host", "test_key")
            
            assert light.id == "test_light_1"
            assert light.state == "true"
            assert light.brightness_level == 50.0
            assert light.colour_temperature == 300
            assert not light._is_plug

    def test_initialize_smart_plug(self, valid_plug_dict):
        """Test initialization of a smart plug with valid data"""
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = {
                "data": [{
                    "on": {"on": 'false'}
                }]
            }
            
            plug = HueLight(valid_plug_dict, "test_host", "test_key")
            
            assert plug.id == "test_plug_1"
            assert plug.state == "false"
            assert plug._is_plug
            # Verify plug doesn't have light-specific attributes
            assert not hasattr(plug, "brightness_level")
            assert not hasattr(plug, "colour_temperature")

    def test_invalid_light_data(self):
        """Test initialization with invalid light data"""
        invalid_dict = {
            "id": "test_light_1",
            "metadata": {
                "name": "Test Light",
                "archetype": "sultanbulb"
            },
            "on": {"on": True}
            # Missing dimming and color_temperature
        }
        
        with pytest.raises(HueValidationError) as exc_info:
            HueLight(invalid_dict, "test_host", "test_key")
        assert "Invalid light device data" in str(exc_info.value)

    def test_turn_on_light(self, valid_light_dict):
        """Test turning on a light"""

        valid_light_dict['on']['on'] = False
        
        with patch('Prometheus.device.HueResource._get') as mock_get, \
             patch('Prometheus.device.HueResource._put') as mock_put:
            
            # Setup initial state
            mock_get.return_value = {
                "data": [{
                    "on": {"on": False},
                    "dimming": {"brightness": 50.0},
                    "color_temperature": {"mirek": 300}
                }]
            }
            
            light = HueLight(valid_light_dict, "test_host", "test_key")
            light.turn_on()
            
            # Verify the PUT request was made correctly
            mock_put.assert_called_once_with(
                light.url,
                light._HEADERS,
                {'on': {'on': True}},
                verify=False
            )
            
            # Verify state was updated
            assert light.state == "true"
            assert light._current_state.is_on == True

    def test_change_brightness_validation(self, valid_light_dict):
        """Test brightness validation and normalization"""
        with patch('Prometheus.device.HueResource._get') as mock_get, \
             patch('Prometheus.device.HueResource._put') as mock_put:
            
            mock_get.return_value = {
                "data": [{
                    "on": {"on": True},
                    "dimming": {"brightness": 50.0},
                    "color_temperature": {"mirek": 300}
                }]
            }
            
            light = HueLight(valid_light_dict, "test_host", "test_key")
            
            # Test with value above maximum
            light.change_brightness(150)
            mock_put.assert_called_with(
                light.url,
                light._HEADERS,
                {"dimming": {"brightness": 100}},
                verify=False
            )
            
            # Test with value below minimum
            light.change_brightness(-10)
            mock_put.assert_called_with(
                light.url,
                light._HEADERS,
                {"dimming": {"brightness": 0}},
                verify=False
            )