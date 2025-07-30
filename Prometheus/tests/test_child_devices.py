import pytest
from unittest.mock import Mock, patch, MagicMock
from ..bridgette import Bridgette
from ..device import HueRoom, HueZone, HueLight
from ..exceptions import HueConnectionError, HueValidationError


@pytest.fixture
def mock_light_data():
    """Mock light data with owner relationships"""
    return {
        "light_1": {
            "id": "light_id_1",
            "metadata": {"name": "Living Room Ceiling", "archetype": "ceiling_horizontal"},
            "owner": {"rid": "device_1", "rtype": "device"},
            "on": {"on": True},
            "dimming": {"brightness": 75.0},
            "color_temperature": {"mirek": 200}
        },
        "light_2": {
            "id": "light_id_2", 
            "metadata": {"name": "Office Desk", "archetype": "desk"},
            "owner": {"rid": "device_2", "rtype": "device"},
            "on": {"on": False},
            "dimming": {"brightness": 50.0},
            "color_temperature": {"mirek": 300}
        },
        "light_3": {
            "id": "light_id_3",
            "metadata": {"name": "Zone Light", "archetype": "floor_lantern"},
            "owner": {"rid": "device_3", "rtype": "device"},
            "on": {"on": True},
            "dimming": {"brightness": 90.0},
            "color_temperature": {"mirek": 150}
        }
    }


@pytest.fixture
def mock_room_data():
    """Mock room data with device children"""
    return {
        "id": "room_1",
        "metadata": {"name": "Living Room", "archetype": "living_room"},
        "children": [
            {"rid": "device_1", "rtype": "device"},
            {"rid": "device_2", "rtype": "device"}
        ],
        "services": [{"rid": "grouped_light_1"}]
    }


@pytest.fixture
def mock_zone_data():
    """Mock zone data with light children (zones store light IDs directly)"""
    return {
        "id": "zone_1", 
        "metadata": {"name": "Office Zone", "archetype": "zone"},
        "children": [
            {"rid": "light_id_2", "rtype": "light"},  # Direct light reference
            {"rid": "light_id_3", "rtype": "light"}
        ],
        "services": [{"rid": "grouped_light_2"}]
    }


class TestChildDeviceMapping:
    """Tests for the child_devices mapping functionality"""
    
    def test_room_child_devices_initialization(self, mock_room_data):
        """Test that room child_devices attribute is properly initialized"""
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = {"data": [{"on": {"on": False}}]}
            
            room = HueRoom(mock_room_data, "test_host", "test_key")
            
            assert hasattr(room, 'child_devices')
            assert isinstance(room.child_devices, dict)
            assert len(room.child_devices) == 0  # Empty until mapping occurs
    
    def test_zone_child_devices_initialization(self, mock_zone_data):
        """Test that zone child_devices attribute is properly initialized"""
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = {"data": [{"on": {"on": False}}]}
            
            zone = HueZone(mock_zone_data, "test_host", "test_key")
            
            assert hasattr(zone, 'child_devices')
            assert isinstance(zone.child_devices, dict)
            assert len(zone.child_devices) == 0  # Empty until mapping occurs

    @patch('Prometheus.bridgette.Bridgette._get_lights')
    @patch('Prometheus.bridgette.Bridgette._get_rooms')
    @patch('Prometheus.bridgette.Bridgette._get_zones')
    @patch('Prometheus.bridgette.Bridgette._get_scenes')
    def test_assign_child_devices_room_mapping(self, mock_scenes, mock_zones, 
                                             mock_rooms, mock_lights, mock_light_data, 
                                             mock_room_data):
        """Test that child devices are correctly mapped to rooms"""
        
        # Create mock lights with proper owner relationships
        mock_light_1 = Mock(spec=HueLight)
        mock_light_1._dev_data = mock_light_data["light_1"]
        mock_light_1.id = "light_id_1"
        
        mock_light_2 = Mock(spec=HueLight)  
        mock_light_2._dev_data = mock_light_data["light_2"]
        mock_light_2.id = "light_id_2"
        
        # Mock the bridge methods
        mock_lights.return_value = {
            "living room ceiling": mock_light_1,
            "office desk": mock_light_2
        }
        
        mock_room = Mock(spec=HueRoom)
        mock_room.id = "room_1"
        mock_room.children = ["device_1", "device_2"]  # Device IDs that match light owners
        mock_room.child_devices = {}
        
        mock_rooms.return_value = {"living room": mock_room}
        mock_zones.return_value = {}
        mock_scenes.return_value = []
        
        mock_config = {'hostname': 'test_host', 'key': 'test_key'}
        with patch('builtins.open'), patch('yaml.load', return_value=mock_config), patch('pathlib.Path.exists', return_value=True):
            # Create bridge and trigger mapping
            bridge = Bridgette()
            
            # Verify mapping occurred correctly
            assert len(mock_room.child_devices) == 2
            assert "living room ceiling" in mock_room.child_devices
            assert "office desk" in mock_room.child_devices
            assert mock_room.child_devices["living room ceiling"] == mock_light_1
            assert mock_room.child_devices["office desk"] == mock_light_2

    @patch('Prometheus.bridgette.Bridgette._get_lights')
    @patch('Prometheus.bridgette.Bridgette._get_rooms') 
    @patch('Prometheus.bridgette.Bridgette._get_zones')
    @patch('Prometheus.bridgette.Bridgette._get_scenes')
    def test_assign_child_devices_zone_mapping(self, mock_scenes, mock_zones,
                                             mock_rooms, mock_lights, mock_light_data):
        """Test that child devices are correctly mapped to zones (using light IDs)"""
        
        # Create mock lights 
        mock_light_2 = Mock(spec=HueLight)
        mock_light_2._dev_data = mock_light_data["light_2"] 
        mock_light_2.id = "light_id_2"
        
        mock_light_3 = Mock(spec=HueLight)
        mock_light_3._dev_data = mock_light_data["light_3"]
        mock_light_3.id = "light_id_3"
        
        mock_lights.return_value = {
            "office desk": mock_light_2,
            "zone light": mock_light_3
        }
        
        mock_zone = Mock(spec=HueZone)
        mock_zone.id = "zone_1"
        mock_zone.children = ["light_id_2", "light_id_3"]  # Light IDs directly
        mock_zone.child_devices = {}
        
        mock_rooms.return_value = {}
        mock_zones.return_value = {"office zone": mock_zone}
        mock_scenes.return_value = []
        
        mock_config = {'hostname': 'test_host', 'key': 'test_key'}
        with patch('builtins.open'), patch('yaml.load', return_value=mock_config), patch('pathlib.Path.exists', return_value=True):
            # Create bridge and trigger mapping
            bridge = Bridgette()
            
            # Verify zone mapping occurred correctly
            assert len(mock_zone.child_devices) == 2
            assert "office desk" in mock_zone.child_devices
            assert "zone light" in mock_zone.child_devices
            assert mock_zone.child_devices["office desk"] == mock_light_2
            assert mock_zone.child_devices["zone light"] == mock_light_3

    @patch('Prometheus.bridgette.Bridgette._get_lights')
    @patch('Prometheus.bridgette.Bridgette._get_rooms')
    @patch('Prometheus.bridgette.Bridgette._get_zones') 
    @patch('Prometheus.bridgette.Bridgette._get_scenes')
    def test_assign_child_devices_mixed_mapping(self, mock_scenes, mock_zones,
                                               mock_rooms, mock_lights, mock_light_data):
        """Test child device mapping with both device IDs and light IDs in zones"""
        
        mock_light_1 = Mock(spec=HueLight)
        mock_light_1._dev_data = mock_light_data["light_1"]
        mock_light_1.id = "light_id_1"
        
        mock_light_2 = Mock(spec=HueLight)
        mock_light_2._dev_data = mock_light_data["light_2"] 
        mock_light_2.id = "light_id_2"
        
        mock_lights.return_value = {
            "living room ceiling": mock_light_1,
            "office desk": mock_light_2
        }
        
        # Zone with mixed ID types
        mock_zone = Mock(spec=HueZone)
        mock_zone.id = "zone_mixed"
        mock_zone.children = [
            "light_id_1",  # Direct light ID
            "device_2"     # Device ID (should match light_2's owner)
        ]
        mock_zone.child_devices = {}
        
        mock_rooms.return_value = {}
        mock_zones.return_value = {"mixed zone": mock_zone}
        mock_scenes.return_value = []
        
        mock_config = {'hostname': 'test_host', 'key': 'test_key'}
        with patch('builtins.open'), patch('yaml.load', return_value=mock_config), patch('pathlib.Path.exists', return_value=True):
            bridge = Bridgette()
            
            # Should handle both types correctly
            assert len(mock_zone.child_devices) == 2
            assert "living room ceiling" in mock_zone.child_devices  # Found by light ID
            assert "office desk" in mock_zone.child_devices  # Found by owner device ID


class TestChildDeviceUsage:
    """Tests for using child_devices functionality"""
    
    def test_child_device_control_access(self):
        """Test that child devices can be accessed and controlled"""
        # Create a real light object for testing
        light_data = {
            "id": "test_light_1",
            "metadata": {"name": "Test Light", "archetype": "ceiling_horizontal"},
            "owner": {"rid": "device_1", "rtype": "device"},
            "on": {"on": True},
            "dimming": {"brightness": 75.0},
            "color_temperature": {"mirek": 200}
        }
        
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = {"data": [light_data]}
            
            light = HueLight(light_data, "test_host", "test_key")
            
            # Create room with child device
            room_data = {
                "id": "test_room",
                "metadata": {"name": "Test Room", "archetype": "living_room"},
                "children": [{"rid": "device_1"}],
                "services": [{"rid": "grouped_light_1"}]
            }
            
            with patch('Prometheus.device.HueResource._get') as mock_room_get:
                mock_room_get.return_value = {"data": [{"on": {"on": False}}]}
                room = HueRoom(room_data, "test_host", "test_key")
                
                # Manually assign child device (simulating bridge mapping)
                room.child_devices["test light"] = light
                
                # Test access and control
                assert "test light" in room.child_devices
                assert isinstance(room.child_devices["test light"], HueLight)
                assert room.child_devices["test light"].state == "True"
                
                # Test that we can call methods on child devices
                with patch('Prometheus.device.HueResource._put') as mock_put:
                    room.child_devices["test light"].turn_off()
                    mock_put.assert_called_once()

    def test_empty_child_devices_handling(self):
        """Test behavior when rooms/zones have no child devices"""
        room_data = {
            "id": "empty_room",
            "metadata": {"name": "Empty Room", "archetype": "living_room"}, 
            "children": [],  # No children
            "services": [{"rid": "grouped_light_1"}]
        }
        
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = {"data": [{"on": {"on": False}}]}
            room = HueRoom(room_data, "test_host", "test_key")
            
            assert len(room.child_devices) == 0
            assert isinstance(room.child_devices, dict)
            
            # Should not raise errors when accessing empty dict
            assert "nonexistent" not in room.child_devices
            assert list(room.child_devices.keys()) == []


class TestChildDeviceIntegration:
    """Integration tests for child_devices with existing functionality"""
    
    def test_child_devices_docstring_updates(self):
        """Test that docstrings properly document child_devices"""
        # Check that HueRoom docstring mentions child_devices
        room_docstring = HueRoom.__doc__
        assert "child_devices" in room_docstring
        assert "Dictionary mapping light names to HueLight objects" in room_docstring
        
        # Check that HueZone docstring mentions child_devices  
        zone_docstring = HueZone.__doc__
        assert "child_devices" in zone_docstring
        assert "Dictionary mapping light names to HueLight objects" in zone_docstring

    def test_child_devices_backwards_compatibility(self):
        """Test that existing functionality still works with child_devices added"""
        room_data = {
            "id": "test_room",
            "metadata": {"name": "Test Room", "archetype": "living_room"},
            "children": [{"rid": "device_1"}],
            "services": [{"rid": "grouped_light_1"}]
        }
        
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = {"data": [{"on": {"on": False}}]}
            room = HueRoom(room_data, "test_host", "test_key")
            
            # All existing attributes should still exist and work
            assert hasattr(room, 'children')
            assert hasattr(room, 'scenes')
            assert hasattr(room, 'state')
            assert hasattr(room, 'grouped_light_id')
            
            # New attribute should also exist
            assert hasattr(room, 'child_devices')
            
            # Existing methods should still work
            with patch('Prometheus.device.HueResource._put'):
                room.turn_off()  # Should not raise errors