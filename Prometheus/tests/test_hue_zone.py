import pytest
from unittest.mock import Mock, patch
from ..device import HueZone
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
        """Test brightness value normalization for out-of-range values."""
        with patch('Prometheus.device.HueResource._get') as mock_get, \
             patch('Prometheus.device.HueResource._put') as mock_put:
            
            mock_get.return_value = {"data": [{"on": {"on": True}}]}
            zone = HueZone(standard_zone_dict, "test_host", "test_key")
            
            # Test above maximum
            zone.change_brightness(150)
            mock_put.assert_called_with(
                url=zone.grouped_light_url,
                headers=zone._HEADERS,
                body={'dimming': {'brightness': 100}}
            )
            
            # Test below minimum
            zone.change_brightness(0)
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