import pytest
from unittest.mock import Mock, patch, MagicMock
from ..bridgette import Bridgette
from ..exceptions import BridgeConfigError, BridgeConnectionError


class TestBridgetteChildDeviceMapping:
    """Tests for Bridgette's child device mapping functionality"""
    
    @patch('Prometheus.bridgette.Bridgette._assign_child_devices')
    @patch('Prometheus.bridgette.Bridgette._assign_scenes')
    @patch('Prometheus.bridgette.Bridgette._get_zones')
    @patch('Prometheus.bridgette.Bridgette._get_rooms') 
    @patch('Prometheus.bridgette.Bridgette._get_lights')
    def test_assign_child_devices_called_during_init(self, mock_get_lights, 
                                                   mock_get_rooms, mock_get_zones,
                                                   mock_assign_scenes, 
                                                   mock_assign_child_devices):
        """Test that _assign_child_devices is called during Bridgette initialization"""
        
        # Mock the required methods
        mock_get_lights.return_value = {}
        mock_get_rooms.return_value = {} 
        mock_get_zones.return_value = {}
        
        mock_config = {'hostname': 'test_host', 'key': 'test_key'}
        with patch('builtins.open'), patch('yaml.load', return_value=mock_config), patch('pathlib.Path.exists', return_value=True):
            bridge = Bridgette()
            
            # Verify _assign_child_devices was called
            mock_assign_child_devices.assert_called_once()
            
            # Verify it's called after _assign_scenes (correct order)
            assert mock_assign_scenes.call_count == 1
            assert mock_assign_child_devices.call_count == 1

    @patch('Prometheus.bridgette.Bridgette._get_scenes')
    @patch('Prometheus.bridgette.Bridgette._get_zones')
    @patch('Prometheus.bridgette.Bridgette._get_rooms')
    @patch('Prometheus.bridgette.Bridgette._get_lights')
    def test_assign_child_devices_implementation(self, mock_get_lights, mock_get_rooms,
                                               mock_get_zones, mock_get_scenes):
        """Test the actual implementation of _assign_child_devices"""
        
        # Create mock lights with different ID types
        mock_light_1 = Mock()
        mock_light_1._dev_data = {"owner": {"rid": "device_1"}}
        mock_light_1.id = "light_1"
        
        mock_light_2 = Mock()
        mock_light_2._dev_data = {"owner": {"rid": "device_2"}}  
        mock_light_2.id = "light_2"
        
        mock_get_lights.return_value = {
            "ceiling light": mock_light_1,
            "desk lamp": mock_light_2
        }
        
        # Create mock room (uses device IDs)
        mock_room = Mock()
        mock_room.id = "room_1"
        mock_room.children = ["device_1", "device_2"]
        mock_room.child_devices = {}
        
        # Create mock zone (uses light IDs) 
        mock_zone = Mock()
        mock_zone.id = "zone_1"
        mock_zone.children = ["light_1", "light_2"]
        mock_zone.child_devices = {}
        
        mock_get_rooms.return_value = {"living room": mock_room}
        mock_get_zones.return_value = {"office zone": mock_zone}
        mock_get_scenes.return_value = []
        
        mock_config = {'hostname': 'test_host', 'key': 'test_key'}
        with patch('builtins.open'), patch('yaml.load', return_value=mock_config), patch('pathlib.Path.exists', return_value=True):
            bridge = Bridgette()
            
            # Verify room mapping (by device ID)
            assert len(mock_room.child_devices) == 2
            assert "ceiling light" in mock_room.child_devices
            assert "desk lamp" in mock_room.child_devices
            assert mock_room.child_devices["ceiling light"] == mock_light_1
            assert mock_room.child_devices["desk lamp"] == mock_light_2
            
            # Verify zone mapping (by light ID)
            assert len(mock_zone.child_devices) == 2
            assert "ceiling light" in mock_zone.child_devices
            assert "desk lamp" in mock_zone.child_devices
            assert mock_zone.child_devices["ceiling light"] == mock_light_1
            assert mock_zone.child_devices["desk lamp"] == mock_light_2

    @patch('Prometheus.bridgette.Bridgette._get_scenes')  
    @patch('Prometheus.bridgette.Bridgette._get_zones')
    @patch('Prometheus.bridgette.Bridgette._get_rooms')
    @patch('Prometheus.bridgette.Bridgette._get_lights')
    def test_assign_child_devices_no_matches(self, mock_get_lights, mock_get_rooms,
                                           mock_get_zones, mock_get_scenes):
        """Test _assign_child_devices when no child devices match"""
        
        # Light with owner that doesn't match any room/zone children
        mock_light = Mock()
        mock_light._dev_data = {"owner": {"rid": "device_999"}}
        mock_light.id = "light_999"
        
        mock_get_lights.return_value = {"orphan light": mock_light}
        
        # Room/zone with children that don't match any light owners/IDs
        mock_room = Mock()
        mock_room.id = "room_2"
        mock_room.children = ["device_1", "device_2"] 
        mock_room.child_devices = {}
        
        mock_zone = Mock()
        mock_zone.id = "zone_2"
        mock_zone.children = ["light_1", "light_2"]
        mock_zone.child_devices = {}
        
        mock_get_rooms.return_value = {"empty room": mock_room}
        mock_get_zones.return_value = {"empty zone": mock_zone}
        mock_get_scenes.return_value = []
        
        mock_config = {'hostname': 'test_host', 'key': 'test_key'}
        with patch('builtins.open'), patch('yaml.load', return_value=mock_config), patch('pathlib.Path.exists', return_value=True):
            bridge = Bridgette()
            
            # Should complete without errors, but no mappings
            assert len(mock_room.child_devices) == 0
            assert len(mock_zone.child_devices) == 0

    @patch('Prometheus.bridgette.Bridgette._get_scenes')
    @patch('Prometheus.bridgette.Bridgette._get_zones')
    @patch('Prometheus.bridgette.Bridgette._get_rooms')
    @patch('Prometheus.bridgette.Bridgette._get_lights')
    def test_assign_child_devices_partial_matches(self, mock_get_lights, mock_get_rooms,
                                                 mock_get_zones, mock_get_scenes):
        """Test _assign_child_devices with partial matches"""
        
        # Create lights where only some match room/zone children
        mock_light_1 = Mock()
        mock_light_1._dev_data = {"owner": {"rid": "device_1"}}  # Will match room
        mock_light_1.id = "light_1"
        
        mock_light_2 = Mock()
        mock_light_2._dev_data = {"owner": {"rid": "device_999"}}  # Won't match anything
        mock_light_2.id = "light_999"
        
        mock_get_lights.return_value = {
            "matching light": mock_light_1,
            "orphan light": mock_light_2
        }
        
        mock_room = Mock()
        mock_room.id = "room_3"
        mock_room.children = ["device_1", "device_2"]  # device_1 matches, device_2 doesn't
        mock_room.child_devices = {}
        
        mock_get_rooms.return_value = {"test room": mock_room}
        mock_get_zones.return_value = {}
        mock_get_scenes.return_value = []
        
        mock_config = {'hostname': 'test_host', 'key': 'test_key'}
        with patch('builtins.open'), patch('yaml.load', return_value=mock_config), patch('pathlib.Path.exists', return_value=True):
            bridge = Bridgette()
            
            # Only the matching light should be mapped
            assert len(mock_room.child_devices) == 1
            assert "matching light" in mock_room.child_devices
            assert "orphan light" not in mock_room.child_devices
            assert mock_room.child_devices["matching light"] == mock_light_1