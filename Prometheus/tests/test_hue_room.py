import pytest
from datetime import datetime
from ..device import HueRoom, HueScene
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

    def test_standard_room_initialization(self, standard_room_dict, hue_http):
        """Verify proper initialization of a standard room"""
        hue_http.mock_get.return_value = {"data": [{"on": {"on": 'false'}}]}
        
        room = HueRoom(standard_room_dict, "test_host", "test_key")
        
        # Verify basic attributes
        assert room.id == "test_room_1"
        assert room.name == "living_room"
        assert room.children == ["light_1", "light_2"]
        assert room.grouped_light_id == "grouped_light_1"
        assert room.state == "false"
        assert isinstance(room.scenes, dict)
        assert len(room.scenes) == 0
        assert isinstance(room.devices, dict)
        assert len(room.devices) == 0

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

    def test_turn_off_from_on_state(self, standard_room_dict, hue_http):
        """Test turning off a room from on state."""
        # Setup: Room starts in ON state
        hue_http.mock_get.return_value = {"data": [{"on": {"on": True}}]}
        
        room = HueRoom(standard_room_dict, "test_host", "test_key")
        room.turn_off()
        
        # Verify the correct PUT request without verify parameter
        hue_http.mock_put.assert_called_once_with(
            url=room.grouped_light_url,
            headers=room._HEADERS,
            body={'on': {'on': False}}
        )
        assert room.state == "false"

    def test_turn_off_network_error(self, standard_room_dict, hue_http):
        """Test handling of network errors during turn off"""
        hue_http.mock_get.return_value = {"data": [{"on": {"on": True}}]}
        hue_http.mock_put.side_effect = Exception("Network error")
        
        room = HueRoom(standard_room_dict, "test_host", "test_key")
        
        with pytest.raises(HueConnectionError) as exc_info:
            room.turn_off()
        assert "Failed to turn off" in str(exc_info.value)

    def test_valid_brightness_change(self, standard_room_dict, hue_http):
        """Test changing brightness to a valid value"""
        hue_http.mock_get.return_value = {"data": [{"on": {"on": True}}]}
        room = HueRoom(standard_room_dict, "test_host", "test_key")
        
        room.change_brightness(75)
        
        hue_http.mock_put.assert_called_once_with(
            url=room.grouped_light_url,
            headers=room._HEADERS,
            body={'dimming': {'brightness': 75}}
        )

    def test_invalid_brightness_type(self, standard_room_dict, hue_http):
        """Test handling of invalid brightness value types"""
        hue_http.mock_get.return_value = {"data": [{"on": {"on": True}}]}
        room = HueRoom(standard_room_dict, "test_host", "test_key")
        
        with pytest.raises(HueValidationError) as exc_info:
            room.change_brightness("50")  # String instead of number
        assert "must be a number" in str(exc_info.value)

    def test_set_smart_scene_success(self, office_room_dict, hue_http):
        """Test successful smart scene activation"""
        hue_http.mock_get.return_value = {"data": [{"on": {"on": True}}]}
        room = HueRoom(office_room_dict, "test_host", "test_key")
        
        # Add test scene as HueScene object
        test_scene_dict = {
            'id': 'scene_1',
            'type': 'smart_scene',
            'metadata': {'name': 'Natural Light'},
            'group': {'rid': 'test_room_2'}
        }
        scene_obj = HueScene(dev_dict=test_scene_dict, hue_hostname="test_host", hue_key="test_key")
        room.scenes = {
            'natural light': scene_obj
        }
        
        room.set_smart_scene('natural light', brightness=80)
        
        hue_http.mock_put.assert_called_once_with(
            url=room.base_url + "smart_scene/scene_1",
            headers=room._HEADERS,
            body={
                'recall': {
                    'action': 'activate',
                    'dimming': {'brightness': 80}
                }
            }
        )

    def test_nonexistent_smart_scene(self, office_room_dict, hue_http):
        """Test handling of attempts to activate nonexistent scenes"""
        hue_http.mock_get.return_value = {"data": [{"on": {"on": True}}]}
        room = HueRoom(office_room_dict, "test_host", "test_key")
        
        with pytest.raises(HueValidationError) as exc_info:
            room.set_smart_scene('nonexistent_scene')
        assert "not found" in str(exc_info.value)