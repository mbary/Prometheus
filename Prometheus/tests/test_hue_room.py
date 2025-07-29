import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from ..device import HueRoom
from ..exceptions import HueConnectionError, HueValidationError, HueResponseError

# First, let's create our test fixtures that we'll reuse across tests
@pytest.fixture
def standard_room_dict():
    """
    Provides configuration for a standard room (like living room).
    This room has basic functionality without special scene requirements.
    """
    return {
        "id": "test_room_1",
        "metadata": {
            "name": "living_room",
            "archetype": "room"
        },
        "services": [
            {"rid": "grouped_light_1"}
        ],
        "children": [
            {"rid": "light_1"},
            {"rid": "light_2"}
        ],
        "on": {"on": 'false'}
    }

@pytest.fixture
def office_room_dict():
    """
    Provides configuration for an office room.
    Office rooms require special handling for the natural light scene.
    """
    return {
        "id": "test_room_2",
        "metadata": {
            "name": "office",
            "archetype": "room"
        },
        "services": [
            {"rid": "grouped_light_2"}
        ],
        "children": [
            {"rid": "light_3"},
            {"rid": "light_4"}
        ],
        "on": {"on": 'false'}
    }

class TestHueRoomInitialization:
    """
    Tests focusing on room initialization and configuration parsing.
    These verify that rooms are properly set up with their required attributes.
    """

    def test_standard_room_initialization(self, standard_room_dict):
        """Verify proper initialization of a standard room"""
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = {"data": [{"on": {"on": 'false'}}]}
            
            room = HueRoom(standard_room_dict, "test_host", "test_key")
            
            # Verify basic attributes
            assert room.id == "test_room_1"
            assert room.name == "living_room"
            assert room.children == ["light_1", "light_2"]
            assert room.grouped_light_id == "grouped_light_1"
            assert room.state == "false"
            assert isinstance(room.scenes, dict)
            assert len(room.scenes) == 0

    def test_invalid_room_configuration(self):
        """Test initialization with invalid room configuration"""
        invalid_dict = {
            "id": "test_room_1",
            "metadata": {
                "name": "test_room"
            }
            # Missing required fields
        }
        
        with pytest.raises(HueValidationError) as exc_info:
            HueRoom(invalid_dict, "test_host", "test_key")
        assert "Invalid room data" in str(exc_info.value)

    def test_turn_off_from_on_state(self, standard_room_dict):


        with patch('Prometheus.device.HueResource._get') as mock_get, \
            patch('Prometheus.device.HueResource._put') as mock_put:
            
            # Setup: Room starts in ON state
            mock_get.return_value = {"data": [{"on": {"on": True}}]}
            
            room = HueRoom(standard_room_dict, "test_host", "test_key")
            room.turn_off()
            
            # Verify the correct PUT request without verify parameter
            mock_put.assert_called_once_with(
                url=room.grouped_light_url,
                headers=room._HEADERS,
                body={'on': {'on': False}}
            )
            assert room.state == "false"

    def test_turn_off_network_error(self, standard_room_dict):
        """Test handling of network errors during turn off"""
        with patch('Prometheus.device.HueResource._get') as mock_get, \
             patch('Prometheus.device.HueResource._put') as mock_put:
            
            mock_get.return_value = {"data": [{"on": {"on": True}}]}
            mock_put.side_effect = Exception("Network error")
            
            room = HueRoom(standard_room_dict, "test_host", "test_key")
            
            with pytest.raises(HueConnectionError) as exc_info:
                room.turn_off()
            assert "Failed to turn off" in str(exc_info.value)

    def test_valid_brightness_change(self, standard_room_dict):
        """Test changing brightness to a valid value"""
        with patch('Prometheus.device.HueResource._get') as mock_get, \
             patch('Prometheus.device.HueResource._put') as mock_put:
            
            mock_get.return_value = {"data": [{"on": {"on": True}}]}
            room = HueRoom(standard_room_dict, "test_host", "test_key")
            
            room.change_brightness(75)
            
            mock_put.assert_called_once_with(
                url=room.grouped_light_url,
                headers=room._HEADERS,
                body={'dimming': {'brightness': 75}}
            )

    def test_invalid_brightness_type(self, standard_room_dict):
        """Test handling of invalid brightness value types"""
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = {"data": [{"on": {"on": True}}]}
            room = HueRoom(standard_room_dict, "test_host", "test_key")
            
            with pytest.raises(HueValidationError) as exc_info:
                room.change_brightness("50")  # String instead of number
            assert "must be a number" in str(exc_info.value)

    def test_set_smart_scene_success(self, office_room_dict):
        """Test successful smart scene activation"""
        with patch('Prometheus.device.HueResource._get') as mock_get, \
             patch('Prometheus.device.HueResource._put') as mock_put:
            
            mock_get.return_value = {"data": [{"on": {"on": True}}]}
            room = HueRoom(office_room_dict, "test_host", "test_key")
            
            # Add test scene
            room.scenes = {
                'natural light': {
                    'id': 'scene_1'
                }
            }
            
            room.set_smart_scene('natural light', brightness=80)
            
            mock_put.assert_called_once_with(
                url=room.base_url + "smart_scene/scene_1",
                headers=room._HEADERS,
                body={
                    'recall': {
                        'action': 'activate',
                        'dimming': {'brightness': 80}
                    }
                }
            )

    def test_nonexistent_smart_scene(self, office_room_dict):
        """Test handling of attempts to activate nonexistent scenes"""
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = {"data": [{"on": {"on": True}}]}
            room = HueRoom(office_room_dict, "test_host", "test_key")
            
            with pytest.raises(HueValidationError) as exc_info:
                room.set_smart_scene('nonexistent_scene')
            assert "not found" in str(exc_info.value)