import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from ..device import HueScene
from ..exceptions import HueConnectionError, HueValidationError, HueResponseError

# Test fixtures for different scene types
@pytest.fixture
def regular_scene_dict():
    """
    Provides configuration for a regular scene.
    This represents a standard user-created scene with specific light settings.
    """
    return {
        "id": "scene_123",
        "id_v1": "/scenes/SMOkmj-BGRy3bzgb",
        "type": "scene",
        "metadata": {
            "name": "Concentrate",
            "image": {"rid": "image_123", "rtype": "public_image"}
        },
        "group": {"rid": "zone_456", "rtype": "zone"},
        "actions": [
            {
                "target": {"rid": "light_1", "rtype": "light"},
                "action": {
                    "on": {"on": True},
                    "dimming": {"brightness": 100.0},
                    "color_temperature": {"mirek": 233}
                }
            }
        ],
        "palette": {
            "color": [],
            "dimming": [],
            "color_temperature": [{"color_temperature": {"mirek": 233}, "dimming": {"brightness": 100.0}}],
            "effects": [],
            "effects_v2": []
        },
        "recall": {},
        "speed": 0.6031746031746031,
        "auto_dynamic": False,
        "status": {"active": "inactive", "last_recall": "2025-07-31T18:17:43.750Z"}
    }

@pytest.fixture
def smart_scene_dict():
    """
    Provides configuration for a smart scene.
    This represents an adaptive scene that changes throughout the day.
    """
    return {
        "id": "smart_scene_789",
        "type": "smart_scene",
        "metadata": {
            "name": "Natural Light",
            "image": {"rid": "image_789", "rtype": "public_image"}
        },
        "group": {"rid": "zone_456", "rtype": "zone"},
        "week_timeslots": [
            {
                "timeslots": [
                    {
                        "start_time": {"kind": "time", "time": {"hour": 7, "minute": 0, "second": 0}},
                        "target": {"rid": "scene_morning", "rtype": "scene"}
                    },
                    {
                        "start_time": {"kind": "sunset", "time": {"hour": 0, "minute": 0, "second": 0}},
                        "target": {"rid": "scene_evening", "rtype": "scene"}
                    }
                ],
                "recurrence": ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
            }
        ],
        "transition_duration": 60000,
        "active_timeslot": {"timeslot_id": 1, "weekday": "thursday"},
        "state": "active"
    }

@pytest.fixture
def custom_scene_dict():
    """
    Provides configuration for a custom user scene.
    This represents a basic scene without advanced features.
    """
    return {
        "id": "custom_scene_999",
        "type": "scene",
        "metadata": {"name": "Custom Scene"},
        "id_v1": "/scenes/paqHwLIyapWR3hUt",
        "actions": [
            {
                "target": {"rid": "light_1", "rtype": "light"},
                "action": {
                    "on": {"on": True},
                    "dimming": {"brightness": 100.0},
                    "gradient": {
                        "points": [
                            {"color": {"xy": {"x": 0.2931, "y": 0.5355}}}
                        ],
                        "mode": "interpolated_palette"
                    }
                }
            }
        ]
    }

@pytest.fixture
def mock_fresh_scene_responses():
    """Fixture providing mock responses for fresh scene data requests"""
    return {
        "regular_active": {
            "data": [{
                "status": {"active": "active", "last_recall": "2025-08-01T12:00:00.000Z"},
                "type": "scene"
            }]
        },
        "regular_inactive": {
            "data": [{
                "status": {"active": "inactive", "last_recall": "2025-08-01T11:00:00.000Z"},
                "type": "scene"
            }]
        },
        "smart_active": {
            "data": [{
                "state": "active",
                "type": "smart_scene",
                "active_timeslot": {"timeslot_id": 2, "weekday": "thursday"}
            }]
        },
        "smart_inactive": {
            "data": [{
                "state": "inactive",
                "type": "smart_scene"
            }]
        },
        "empty_response": {"data": []},
        "error_response": {"errors": ["Scene not found"]}
    }


class TestHueSceneInitialization:
    """Test suite for HueScene initialization and configuration parsing."""

    def test_regular_scene_initialization(self, regular_scene_dict):
        """Test initialization of a regular scene with complete data"""
        scene = HueScene(regular_scene_dict, "test_host", "test_key")
        
        # Verify core attributes
        assert scene.id == "scene_123"
        assert scene.name == "concentrate"
        assert scene.scene_type == "scene"
        assert scene.url == scene.base_url + "scene/scene_123"
        
        # Verify metadata includes all scene information
        assert "actions" in scene.metadata
        assert "palette" in scene.metadata
        assert "status" in scene.metadata
        assert scene.metadata["id_v1"] == "/scenes/SMOkmj-BGRy3bzgb"
        assert scene.metadata["speed"] == 0.6031746031746031

    def test_smart_scene_initialization(self, smart_scene_dict):
        """Test initialization of a smart scene with complete data"""
        scene = HueScene(smart_scene_dict, "test_host", "test_key")
        
        # Verify core attributes
        assert scene.id == "smart_scene_789"
        assert scene.name == "natural light"
        assert scene.scene_type == "smart_scene"
        assert scene.url == scene.base_url + "smart_scene/smart_scene_789"
        
        # Verify metadata includes smart scene specific data
        assert "week_timeslots" in scene.metadata
        assert "transition_duration" in scene.metadata
        assert "state" in scene.metadata
        assert scene.metadata["active_timeslot"]["timeslot_id"] == 1

    def test_custom_scene_initialization(self, custom_scene_dict):
        """Test initialization of a minimal custom scene"""
        scene = HueScene(custom_scene_dict, "test_host", "test_key")
        
        # Verify core attributes with minimal data
        assert scene.id == "custom_scene_999"
        assert scene.name == "custom scene"  # From metadata name
        assert scene.scene_type == "scene"
        assert scene.url == scene.base_url + "scene/custom_scene_999"
        
        # Verify metadata contains actions
        assert "actions" in scene.metadata
        assert len(scene.metadata["actions"]) == 1

    def test_invalid_scene_data_missing_id(self):
        """Test initialization with missing required ID field"""
        invalid_dict = {
            "type": "scene",
            "metadata": {"name": "Test Scene"}
            # Missing id field
        }
        
        with pytest.raises(HueValidationError) as exc_info:
            HueScene(invalid_dict, "test_host", "test_key")
        assert "Missing required fields" in str(exc_info.value)

    def test_invalid_scene_data_empty_dict(self):
        """Test initialization with completely empty data"""
        with pytest.raises(HueValidationError) as exc_info:
            HueScene({}, "test_host", "test_key")
        assert "Missing required fields" in str(exc_info.value)

    def test_scene_name_normalization(self, regular_scene_dict):
        """Test that scene names are properly normalized to lowercase"""
        regular_scene_dict["metadata"]["name"] = "BRIGHT FOCUS Scene"
        scene = HueScene(regular_scene_dict, "test_host", "test_key")
        
        assert scene.name == "bright focus scene"


class TestHueSceneProperties:
    """Test suite for HueScene property access and type detection."""

    def test_type_property_regular_scene(self, regular_scene_dict):
        """Test type property returns correct value for regular scene"""
        scene = HueScene(regular_scene_dict, "test_host", "test_key")
        assert scene.type == "scene"

    def test_type_property_smart_scene(self, smart_scene_dict):
        """Test type property returns correct value for smart scene"""
        scene = HueScene(smart_scene_dict, "test_host", "test_key")
        assert scene.type == "smart_scene"

    def test_metadata_property_access(self, regular_scene_dict):
        """Test that metadata property provides access to all scene data"""
        scene = HueScene(regular_scene_dict, "test_host", "test_key")
        
        # Test accessing various metadata fields
        assert scene.metadata["actions"] == regular_scene_dict["actions"]
        assert scene.metadata["palette"] == regular_scene_dict["palette"]
        assert scene.metadata["auto_dynamic"] == regular_scene_dict["auto_dynamic"]


class TestHueSceneStatusMonitoring:
    """Test suite for HueScene live status monitoring functionality."""

    def test_status_regular_scene_active(self, regular_scene_dict, mock_fresh_scene_responses):
        """Test status property for active regular scene with fresh data"""
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = mock_fresh_scene_responses["regular_active"]
            
            scene = HueScene(regular_scene_dict, "test_host", "test_key")
            status = scene.status
            
            assert status == "on"
            mock_get.assert_called_once_with(scene.url)

    def test_status_regular_scene_inactive(self, regular_scene_dict, mock_fresh_scene_responses):
        """Test status property for inactive regular scene"""
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = mock_fresh_scene_responses["regular_inactive"]
            
            scene = HueScene(regular_scene_dict, "test_host", "test_key")
            status = scene.status
            
            assert status == "off"
            mock_get.assert_called_once_with(scene.url)

    def test_status_smart_scene_active(self, smart_scene_dict, mock_fresh_scene_responses):
        """Test status property for active smart scene"""
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = mock_fresh_scene_responses["smart_active"]
            
            scene = HueScene(smart_scene_dict, "test_host", "test_key")
            status = scene.status
            
            assert status == "on"
            mock_get.assert_called_once_with(scene.url)

    def test_status_smart_scene_inactive(self, smart_scene_dict, mock_fresh_scene_responses):
        """Test status property for inactive smart scene"""
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = mock_fresh_scene_responses["smart_inactive"]
            
            scene = HueScene(smart_scene_dict, "test_host", "test_key")
            status = scene.status
            
            assert status == "off"
            mock_get.assert_called_once_with(scene.url)

    def test_status_fallback_to_cached_data_on_error(self, regular_scene_dict):
        """Test status property falls back to cached data when API call fails"""
        # Setup scene with cached inactive status
        regular_scene_dict["status"] = {"active": "inactive"}
        
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            scene = HueScene(regular_scene_dict, "test_host", "test_key")
            status = scene.status
             
            assert status == "off"  # Should use cached data
            mock_get.assert_called_once_with(scene.url)

    def test_status_fallback_to_cached_data_empty_response(self, smart_scene_dict, mock_fresh_scene_responses):
        """Test status property falls back to cached data when response is empty"""
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = mock_fresh_scene_responses["empty_response"]
            
            # Smart scene starts active in cached data
            scene = HueScene(smart_scene_dict, "test_host", "test_key")
            status = scene.status
            
            assert status == "on"  # Should use cached data
            mock_get.assert_called_once_with(scene.url)

    def test_status_handles_malformed_response(self, regular_scene_dict):
        """Test status property handles malformed API responses gracefully"""
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = {"data": [{"invalid": "structure"}]}
            
            scene = HueScene(regular_scene_dict, "test_host", "test_key")
            status = scene.status
            
            # Should fall back to cached data
            assert status == "off"  # Based on fixture data
            mock_get.assert_called_once_with(scene.url)


class TestHueSceneControl:
    """Test suite for HueScene turn_on/turn_off functionality."""

    def test_turn_on_regular_scene(self, regular_scene_dict):
        """Test turning on a regular scene"""
        with patch('Prometheus.device.HueResource._put') as mock_put:
            scene = HueScene(regular_scene_dict, "test_host", "test_key")
            scene.turn_on()
            
            expected_url = scene.base_url + "scene/scene_123"
            expected_body = {"recall": {"action": "active"}}
            
            mock_put.assert_called_once_with(
                url=expected_url,
                headers=scene._HEADERS,
                body=expected_body
            )

    def test_turn_on_smart_scene(self, smart_scene_dict):
        """Test turning on a smart scene"""
        with patch('Prometheus.device.HueResource._put') as mock_put:
            scene = HueScene(smart_scene_dict, "test_host", "test_key")
            scene.turn_on()
            
            expected_url = scene.base_url + "smart_scene/smart_scene_789"
            expected_body = {"recall": {"action": "activate"}}
            
            mock_put.assert_called_once_with(
                url=expected_url,
                headers=scene._HEADERS,
                body=expected_body
            )

    def test_turn_off_regular_scene(self, regular_scene_dict):
        """Test turning off a regular scene"""
        with patch('Prometheus.device.HueResource._put') as mock_put:
            scene = HueScene(regular_scene_dict, "test_host", "test_key")
            scene.turn_off()
            
            # Should turn off the associated group's lights
            expected_url = scene.base_url + "grouped_light/zone_456"
            expected_body = {"on": {"on": False}}
            
            mock_put.assert_called_once_with(
                url=expected_url,
                headers=scene._HEADERS,
                body=expected_body
            )

    def test_turn_off_smart_scene(self, smart_scene_dict):
        """Test turning off a smart scene"""
        with patch('Prometheus.device.HueResource._put') as mock_put:
            scene = HueScene(smart_scene_dict, "test_host", "test_key")
            scene.turn_off()
            
            # Should turn off the associated group's lights
            expected_url = scene.base_url + "grouped_light/zone_456"
            expected_body = {"on": {"on": False}}
            
            mock_put.assert_called_once_with(
                url=expected_url,
                headers=scene._HEADERS,
                body=expected_body
            )

    def test_turn_on_network_error(self, regular_scene_dict):
        """Test handling of network errors during turn_on"""
        with patch('Prometheus.device.HueResource._put') as mock_put:
            mock_put.side_effect = Exception("Network timeout")
            
            scene = HueScene(regular_scene_dict, "test_host", "test_key")
            
            with pytest.raises(HueConnectionError) as exc_info:
                scene.turn_on()
            assert "Failed to turn on scene" in str(exc_info.value)
            assert "concentrate" in str(exc_info.value)

    def test_turn_off_network_error(self, smart_scene_dict):
        """Test handling of network errors during turn_off"""
        with patch('Prometheus.device.HueResource._put') as mock_put:
            mock_put.side_effect = Exception("Connection refused")
            
            scene = HueScene(smart_scene_dict, "test_host", "test_key")
            
            with pytest.raises(HueConnectionError) as exc_info:
                scene.turn_off()
            # The turn_off method doesn't specify error message format, so just check for any error
            assert "Connection refused" in str(exc_info.value) or "Failed" in str(exc_info.value)


class TestHueSceneEdgeCases:
    """Test suite for HueScene edge cases and error conditions."""

    def test_scene_with_missing_metadata_name(self):
        """Test scene initialization when metadata name is missing"""
        scene_dict = {
            "id": "scene_no_name",
            "type": "scene",
            "metadata": {}  # No name field
        }
        
        with pytest.raises(HueValidationError) as exc_info:
            HueScene(scene_dict, "test_host", "test_key")
        assert "Scene missing required 'name' in metadata" in str(exc_info.value)

    def test_scene_with_none_metadata(self):
        """Test scene initialization when metadata is None"""
        scene_dict = {
            "id": "scene_null_meta",
            "type": "scene"
            # No metadata field at all
        }
        
        with pytest.raises(HueValidationError) as exc_info:
            HueScene(scene_dict, "test_host", "test_key")
        assert "Missing required fields" in str(exc_info.value)

    def test_regular_scene_status_with_non_dict_status(self, regular_scene_dict):
        """Test regular scene status handling when status field is not a dict"""
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = {"data": [{"status": "invalid_format"}]}
            
            scene = HueScene(regular_scene_dict, "test_host", "test_key")
            status = scene.status
            
            # Should fall back to cached data
            assert status == "off"

    def test_status_multiple_api_calls_same_result(self, regular_scene_dict, mock_fresh_scene_responses):
        """Test that status property makes API call each time (no caching)"""
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = mock_fresh_scene_responses["regular_active"]
            
            scene = HueScene(regular_scene_dict, "test_host", "test_key")
            
            # Call status multiple times
            status1 = scene.status
            status2 = scene.status
            
            assert status1 == "on"
            assert status2 == "on"
            assert mock_get.call_count == 2  # Should make fresh API call each time

    def test_scene_url_construction_edge_cases(self):
        """Test URL construction for edge case scene types"""
        # Test with custom type that should default to regular scene
        scene_dict = {
            "id": "test_scene",
            "type": "unknown_type",
            "metadata": {"name": "Test"}
        }
        
        scene = HueScene(scene_dict, "test_host", "test_key")
        assert scene.url == scene.base_url + "scene/test_scene"


class TestHueSceneIntegration:
    """Test suite for HueScene integration with other components."""

    def test_scene_works_with_room_integration(self, regular_scene_dict):
        """Test that HueScene objects work correctly when used in room contexts"""
        # This simulates how scenes are used in HueRoom.set_scene() method
        scene = HueScene(regular_scene_dict, "test_host", "test_key") 
        
        # Verify the scene can be accessed like a dictionary (backward compatibility)
        assert scene.id == "scene_123"
        assert scene.type == "scene"
        
        # Test that the scene URL is constructed correctly for API calls
        expected_url = "https://test_host/clip/v2/resource/scene/scene_123"
        assert scene.url == expected_url

    def test_scene_metadata_preservation(self, smart_scene_dict):
        """Test that all original scene data is preserved in metadata"""
        original_keys = set(smart_scene_dict.keys())
        scene = HueScene(smart_scene_dict, "test_host", "test_key")
        
        # All original data should be preserved in metadata (except basic fields)
        preserved_keys = set(scene.metadata.keys())
        
        # Should have most keys, with some transformed (id, metadata, type handled specially)
        expected_keys = original_keys - {"id", "metadata", "type"}
        assert expected_keys.issubset(preserved_keys)
        
    def test_scene_name_access_case_insensitive(self, regular_scene_dict):
        """Test that scene names are stored in lowercase for consistent access"""
        regular_scene_dict["metadata"]["name"] = "Bright CONCENTRATE Mode"
        scene = HueScene(regular_scene_dict, "test_host", "test_key")
        
        assert scene.name == "bright concentrate mode"