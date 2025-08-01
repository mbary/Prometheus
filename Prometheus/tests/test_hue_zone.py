import pytest
from unittest.mock import Mock, patch
from ..device import HueZone, HueScene
from ..exceptions import HueConnectionError, HueValidationError, HueResponseError

@pytest.fixture
def standard_zone_dict():
    """
    Provides a standard zone configuration for testing.
    This represents a typical living room zone with multiple lights.
    """
    return {
        "id": "test_zone_1",
        "metadata": {
            "name": "living_room",
            "archetype": "zone"
        },
        "services": [
            {"rid": "grouped_light_1"}
        ],
        "children": [
            {"rid": "light_1"},
            {"rid": "light_2"}
        ],
        "on": {"on": False}
    }

@pytest.fixture
def office_zone_dict():
    """
    Provides an office zone configuration for testing.
    Office zones require special handling for natural light scenes.
    """
    return {
        "id": "test_zone_2",
        "metadata": {
            "name": "office",
            "archetype": "zone"
        },
        "services": [
            {"rid": "grouped_light_2"}
        ],
        "children": [
            {"rid": "light_3"},
            {"rid": "light_4"}
        ],
        "on": {"on": False}
    }

class TestHueZoneInitialization:
    """Tests for HueZone initialization and configuration parsing."""

    def test_valid_zone_initialization(self, standard_zone_dict):
        """Verify that a zone initializes properly with valid configuration."""
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = {"data": [{"on": {"on": 'false'}}]}
            
            zone = HueZone(standard_zone_dict, "test_host", "test_key")
            
            # Verify core attributes are set correctly
            assert zone.id == "test_zone_1"
            assert zone.name == "living_room"
            assert zone.children == ["light_1", "light_2"]
            assert zone.grouped_light_id == "grouped_light_1"
            assert zone.state == "false"
            assert isinstance(zone.scenes, dict)
            assert len(zone.scenes) == 0
            assert isinstance(zone.devices, dict)
            assert len(zone.devices) == 0

    def test_empty_zone_initialization(self):
        """Verify that initializing a zone without devices raises appropriate error."""
        invalid_dict = {
            "id": "test_zone_1",
            "metadata": {
                "name": "empty_zone",
                "archetype": "zone"
            },
            "services": [{"rid": "grouped_light_1"}]
            # Missing children field
        }
        
        with pytest.raises(HueValidationError) as exc_info:
            HueZone(invalid_dict, "test_host", "test_key")
        assert "appears to be empty" in str(exc_info.value)

class TestHueZoneStateControl:
    """Tests for zone state management (on/off control)."""

    def test_turn_off_success(self, standard_zone_dict):
        """Test successful zone turn off operation."""
        with patch('Prometheus.device.HueResource._get') as mock_get, \
             patch('Prometheus.device.HueResource._put') as mock_put:
            
            # Setup: Zone starts in ON state
            mock_get.return_value = {"data": [{"on": {"on": True}}]}
            
            zone = HueZone(standard_zone_dict, "test_host", "test_key")
            zone.turn_off()
            
            # Verify correct API call
            mock_put.assert_called_once_with(
                zone.grouped_light_url,
                zone._HEADERS,
                {'on': {'on': False}}
            )
            assert zone.state == "false"

    def test_turn_off_connection_error(self, standard_zone_dict):
        """Test handling of connection error during turn off."""
        with patch('Prometheus.device.HueResource._get') as mock_get, \
             patch('Prometheus.device.HueResource._put') as mock_put:
            
            mock_get.return_value = {"data": [{"on": {"on": True}}]}
            mock_put.side_effect = Exception("Network error")
            
            zone = HueZone(standard_zone_dict, "test_host", "test_key")
            
            with pytest.raises(HueConnectionError) as exc_info:
                zone.turn_off()
            assert "Failed to turn off" in str(exc_info.value)
            assert "living_room" in str(exc_info.value)

class TestHueZoneBrightnessControl:
    """Tests for zone brightness control."""

    def test_valid_brightness_change(self, standard_zone_dict):
        """Test successful brightness change within valid range."""
        with patch('Prometheus.device.HueResource._get') as mock_get, \
             patch('Prometheus.device.HueResource._put') as mock_put:
            
            mock_get.return_value = {"data": [{"on": {"on": True}}]}
            zone = HueZone(standard_zone_dict, "test_host", "test_key")
            
            zone.change_brightness(75)
            
            mock_put.assert_called_once_with(
                url=zone.grouped_light_url,
                headers=zone._HEADERS,
                body={'dimming': {'brightness': 75}}
            )

    def test_brightness_normalization(self, standard_zone_dict):
        """Test brightness value normalization for various out-of-range values."""
        with patch('Prometheus.device.HueResource._get') as mock_get, \
             patch('Prometheus.device.HueResource._put') as mock_put:
            
            mock_get.return_value = {"data": [{"on": {"on": True}}]}
            zone = HueZone(standard_zone_dict, "test_host", "test_key")
            
            # Test above maximum (moderate)
            zone.change_brightness(150)
            mock_put.assert_called_with(
                url=zone.grouped_light_url,
                headers=zone._HEADERS,
                body={'dimming': {'brightness': 100}}
            )
            
            # Test above maximum (extreme)
            zone.change_brightness(999)
            mock_put.assert_called_with(
                url=zone.grouped_light_url,
                headers=zone._HEADERS,
                body={'dimming': {'brightness': 100}}
            )
            
            # Test at minimum boundary
            zone.change_brightness(0)
            mock_put.assert_called_with(
                url=zone.grouped_light_url,
                headers=zone._HEADERS,
                body={'dimming': {'brightness': 1}}
            )
            
            # Test below minimum (negative)
            zone.change_brightness(-50)
            mock_put.assert_called_with(
                url=zone.grouped_light_url,
                headers=zone._HEADERS,
                body={'dimming': {'brightness': 1}}
            )

    def test_invalid_brightness_type(self, standard_zone_dict):
        """Test handling of invalid brightness value type."""
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = {"data": [{"on": {"on": True}}]}
            zone = HueZone(standard_zone_dict, "test_host", "test_key")
            
            with pytest.raises(HueValidationError) as exc_info:
                zone.change_brightness("50")  # String instead of number
            assert "must be a number" in str(exc_info.value)


class TestHueZoneTurnOnBehavior:
    """Tests for zone turn-on behavior including special office handling."""

    def test_turn_on_standard_zone(self, standard_zone_dict):
        """Test turning on a standard zone (non-office)."""
        with patch('Prometheus.device.HueResource._get') as mock_get, \
             patch('Prometheus.device.HueResource._put') as mock_put:
            
            mock_get.return_value = {"data": [{"on": {"on": False}}]}
            zone = HueZone(standard_zone_dict, "test_host", "test_key")
            
            zone.turn_on()
            
            # Should simply turn on the grouped light
            mock_put.assert_called_once_with(
                url=zone.grouped_light_url,
                headers=zone._HEADERS,
                body={'on': {'on': True}}
            )
            assert zone.state == "true"

    def test_turn_on_office_zone_with_natural_light_scene(self, office_zone_dict):
        """Test turning on office zone activates natural light scene."""
        with patch('Prometheus.device.HueResource._get') as mock_get, \
             patch('Prometheus.device.HueResource._put') as mock_put:
            
            mock_get.return_value = {"data": [{"on": {"on": False}}]}
            zone = HueZone(office_zone_dict, "test_host", "test_key")
            
            # Add natural light scene
            test_scene_dict = {
                'id': 'natural_light_scene',
                'type': 'smart_scene',
                'metadata': {'name': 'Natural Light'},
                'group': {'rid': 'test_zone_2'}
            }
            scene_obj = HueScene(dev_dict=test_scene_dict, hue_hostname="test_host", hue_key="test_key")
            zone.scenes = {'natural light': scene_obj}
            
            zone.turn_on()
            
            # Should activate the natural light smart scene
            mock_put.assert_called_once_with(
                url=zone.base_url + "smart_scene/natural_light_scene",
                headers=zone._HEADERS,
                body={'recall': {'action': 'activate'}}
            )

    def test_turn_on_office_zone_error_without_scene(self, office_zone_dict):
        """Test office zone raises error when natural light scene missing."""
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = {"data": [{"on": {"on": False}}]}
            zone = HueZone(office_zone_dict, "test_host", "test_key")
            # No scenes added - should raise error
            
            with pytest.raises(HueConnectionError) as exc_info:
                zone.turn_on()
            assert "Failed to turn on office zone" in str(exc_info.value)
            assert "not found" in str(exc_info.value)

    def test_turn_on_network_error(self, standard_zone_dict):
        """Test handling of network error during turn on."""
        with patch('Prometheus.device.HueResource._get') as mock_get, \
             patch('Prometheus.device.HueResource._put') as mock_put:
            
            mock_get.return_value = {"data": [{"on": {"on": False}}]}
            mock_put.side_effect = Exception("Network timeout")
            
            zone = HueZone(standard_zone_dict, "test_host", "test_key")
            
            with pytest.raises(HueConnectionError) as exc_info:
                zone.turn_on()
            assert "Failed to turn on" in str(exc_info.value)
            assert "living_room" in str(exc_info.value)


class TestHueZoneSceneManagement:
    """Tests for zone scene activation and management."""

    def test_set_scene_success(self, standard_zone_dict):
        """Test successful regular scene activation."""
        with patch('Prometheus.device.HueResource._get') as mock_get, \
             patch('Prometheus.device.HueResource._put') as mock_put:
            
            mock_get.return_value = {"data": [{"on": {"on": True}}]}
            zone = HueZone(standard_zone_dict, "test_host", "test_key")
            
            # Add test scene
            test_scene_dict = {
                'id': 'relax_scene',
                'type': 'scene',
                'metadata': {'name': 'Relax'},
                'group': {'rid': 'test_zone_1'}
            }
            scene_obj = HueScene(dev_dict=test_scene_dict, hue_hostname="test_host", hue_key="test_key")
            zone.scenes = {'relax': scene_obj}
            
            zone.set_scene('relax', brightness=50)
            
            mock_put.assert_called_once_with(
                url=zone.base_url + "scene/relax_scene",
                headers=zone._HEADERS,
                body={'recall': {'action': 'active', 'dimming': {'brightness': 50}}}
            )

    def test_set_smart_scene_success(self, office_zone_dict):
        """Test successful smart scene activation."""
        with patch('Prometheus.device.HueResource._get') as mock_get, \
             patch('Prometheus.device.HueResource._put') as mock_put:
            
            mock_get.return_value = {"data": [{"on": {"on": True}}]}
            zone = HueZone(office_zone_dict, "test_host", "test_key")
            
            # Add test smart scene
            test_scene_dict = {
                'id': 'energize_scene',
                'type': 'smart_scene', 
                'metadata': {'name': 'Energize'},
                'group': {'rid': 'test_zone_2'}
            }
            scene_obj = HueScene(dev_dict=test_scene_dict, hue_hostname="test_host", hue_key="test_key")
            zone.scenes = {'energize': scene_obj}
            
            zone.set_smart_scene('energize', brightness=90)
            
            mock_put.assert_called_once_with(
                url=zone.base_url + "smart_scene/energize_scene",
                headers=zone._HEADERS,
                body={'recall': {'action': 'activate', 'dimming': {'brightness': 90}}}
            )

    @pytest.mark.parametrize("zone_fixture,method_name,scene_name", [
        ("standard_zone_dict", "set_scene", "nonexistent_scene"),
        ("office_zone_dict", "set_smart_scene", "nonexistent_smart_scene")
    ])
    def test_scene_not_found_error(self, zone_fixture, method_name, scene_name, request):
        """Test handling of scene not found errors for both regular and smart scenes."""
        zone_dict = request.getfixturevalue(zone_fixture)
        
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = {"data": [{"on": {"on": True}}]}
            zone = HueZone(zone_dict, "test_host", "test_key")
            
            method = getattr(zone, method_name)
            with pytest.raises(HueValidationError) as exc_info:
                method(scene_name)
            assert "not found" in str(exc_info.value)

    def test_set_scene_network_error(self, standard_zone_dict):
        """Test handling of network error during scene activation."""
        with patch('Prometheus.device.HueResource._get') as mock_get, \
             patch('Prometheus.device.HueResource._put') as mock_put:
            
            mock_get.return_value = {"data": [{"on": {"on": True}}]}
            mock_put.side_effect = Exception("Connection failed")
            
            zone = HueZone(standard_zone_dict, "test_host", "test_key")
            
            # Add test scene
            test_scene_dict = {
                'id': 'test_scene',
                'type': 'scene',
                'metadata': {'name': 'Test'},
                'group': {'rid': 'test_zone_1'}
            }
            scene_obj = HueScene(dev_dict=test_scene_dict, hue_hostname="test_host", hue_key="test_key")
            zone.scenes = {'test': scene_obj}
            
            with pytest.raises(HueConnectionError) as exc_info:
                zone.set_scene('test')
            assert "Failed to set scene" in str(exc_info.value)


class TestHueZoneDeviceMapping:
    """Tests for zone device mapping and management."""

    def test_zone_initialization_attributes(self, standard_zone_dict):
        """Test that zone devices, scenes dictionaries and children are properly initialized."""
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = {"data": [{"on": {"on": False}}]}
            zone = HueZone(standard_zone_dict, "test_host", "test_key")
            
            # Verify devices dict is initialized and empty
            assert hasattr(zone, 'devices')
            assert isinstance(zone.devices, dict)
            assert len(zone.devices) == 0
            
            # Verify scenes dict is initialized and empty
            assert hasattr(zone, 'scenes')
            assert isinstance(zone.scenes, dict)
            assert len(zone.scenes) == 0
            
            # Verify children are extracted correctly
            assert zone.children == ["light_1", "light_2"]
            assert len(zone.children) == 2


class TestHueZoneValidation:
    """Tests for zone validation and error handling."""

    def test_invalid_zone_missing_services(self):
        """Test zone validation when services are missing."""
        invalid_dict = {
            "id": "test_zone_1",
            "metadata": {
                "name": "invalid_zone",
                "archetype": "zone"
            },
            "children": [{"rid": "light_1"}]
            # Missing services field
        }
        
        with pytest.raises(HueValidationError) as exc_info:
            HueZone(invalid_dict, "test_host", "test_key")
        assert "Invalid zone data" in str(exc_info.value)


    def test_zone_scene_brightness_validation(self, standard_zone_dict):
        """Test scene activation with invalid brightness values."""
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = {"data": [{"on": {"on": True}}]}
            zone = HueZone(standard_zone_dict, "test_host", "test_key")
            
            # Add test scene
            test_scene_dict = {
                'id': 'test_scene',
                'type': 'scene',
                'metadata': {'name': 'Test'},
                'group': {'rid': 'test_zone_1'}
            }
            scene_obj = HueScene(dev_dict=test_scene_dict, hue_hostname="test_host", hue_key="test_key")
            zone.scenes = {'test': scene_obj}
            
            with pytest.raises(HueValidationError) as exc_info:
                zone.set_scene('test', brightness="invalid")
            assert "must be a number" in str(exc_info.value)