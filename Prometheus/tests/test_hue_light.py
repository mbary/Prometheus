import pytest
from datetime import datetime
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

    def test_initialize_regular_light(self, valid_light_dict, hue_http):
        """Test initialization of a regular light with valid data"""
        hue_http.mock_get.return_value = {
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

    def test_initialize_smart_plug(self, valid_plug_dict, hue_http):
        """Test initialization of a smart plug with valid data"""
        hue_http.mock_get.return_value = {
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

    def test_turn_on_light(self, valid_light_dict, hue_http):
        """Test turning on a light"""
        valid_light_dict['on']['on'] = False
        
        # Setup initial state
        hue_http.mock_get.return_value = {
            "data": [{
                "on": {"on": False},
                "dimming": {"brightness": 50.0},
                "color_temperature": {"mirek": 300}
            }]
        }
        
        light = HueLight(valid_light_dict, "test_host", "test_key")
        light.turn_on()
        
        # Verify the PUT request was made correctly
        hue_http.mock_put.assert_called_once_with(
            light.url,
            light._HEADERS,
            {'on': {'on': True}}
        )
        
        # Verify state was updated
        assert light.state == "true"
        assert light._current_state.is_on == True

    @pytest.mark.parametrize("input_brightness,expected_brightness,description", [
        (150, 100, "above maximum"),
        (200, 100, "well above maximum"),
        (-10, 0, "below minimum"),
        (-50, 0, "well below minimum")
    ])
    def test_change_brightness_validation(self, valid_light_dict, hue_http, input_brightness, expected_brightness, description):
        """Test brightness validation and normalization for out-of-range values."""
        hue_http.mock_get.return_value = {
            "data": [{
                "on": {"on": True},
                "dimming": {"brightness": 50.0},
                "color_temperature": {"mirek": 300}
            }]
        }
        
        light = HueLight(valid_light_dict, "test_host", "test_key")
        
        light.change_brightness(input_brightness)
        hue_http.mock_put.assert_called_with(
            light.url,
            light._HEADERS,
            {"dimming": {"brightness": expected_brightness}}
        )