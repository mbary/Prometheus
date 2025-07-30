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


class TestDeviceMapping:
    """Tests for the devices mapping functionality"""
    
    def test_room_devices_initialization(self, mock_room_data):
        """Test that room devices attribute is properly initialized"""
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = {"data": [{"on": {"on": False}}]}
            
            room = HueRoom(mock_room_data, "test_host", "test_key")
            
            assert hasattr(room, 'devices')
            assert isinstance(room.devices, dict)
            assert len(room.devices) == 0  # Empty until mapping occurs
    
    def test_zone_devices_initialization(self, mock_zone_data):
        """Test that zone devices attribute is properly initialized"""
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = {"data": [{"on": {"on": False}}]}
            
            zone = HueZone(mock_zone_data, "test_host", "test_key")
            
            assert hasattr(zone, 'devices')
            assert isinstance(zone.devices, dict)
            assert len(zone.devices) == 0  # Empty until mapping occurs

    @patch('Prometheus.bridgette.Bridgette._get_lights')
    @patch('Prometheus.bridgette.Bridgette._get_rooms')
    @patch('Prometheus.bridgette.Bridgette._get_zones')
    @patch('Prometheus.bridgette.Bridgette._get_scenes')
    def test_assign_devices_room_mapping(self, mock_scenes, mock_zones, 
                                             mock_rooms, mock_lights, mock_light_data, 
                                             mock_room_data):
        """Test that devices are correctly mapped to rooms"""
        
        # Create mock lights with proper owner relationships
        mock_light_1 = Mock(spec=HueLight)
        mock_light_1._dev_data = mock_light_data["light_1"]
        mock_light_1.id = "light_id_1"
        mock_light_1.name = "living room ceiling"
        
        mock_light_2 = Mock(spec=HueLight)  
        mock_light_2._dev_data = mock_light_data["light_2"]
        mock_light_2.id = "light_id_2"
        mock_light_2.name = "office desk"
        
        # Mock the bridge methods
        mock_lights.return_value = {
            "light_id_1": mock_light_1,
            "light_id_2": mock_light_2
        }
        
        mock_room = Mock(spec=HueRoom)
        mock_room.id = "room_1"
        mock_room.children = ["device_1", "device_2"]  # Device IDs that match light owners
        mock_room.devices = {}
        
        mock_room.name = "living room"
        mock_rooms.return_value = {"room_1": mock_room}
        mock_zones.return_value = {}
        mock_scenes.return_value = []
        
        mock_config = {'hostname': 'test_host', 'key': 'test_key'}
        with patch('builtins.open'), patch('yaml.load', return_value=mock_config), patch('pathlib.Path.exists', return_value=True):
            # Create bridge and trigger mapping
            bridge = Bridgette()
            
            # Verify mapping occurred correctly
            assert len(mock_room.devices) == 2
            assert "living room ceiling" in mock_room.devices
            assert "office desk" in mock_room.devices
            assert mock_room.devices["living room ceiling"] == mock_light_1
            assert mock_room.devices["office desk"] == mock_light_2

    @patch('Prometheus.bridgette.Bridgette._get_lights')
    @patch('Prometheus.bridgette.Bridgette._get_rooms') 
    @patch('Prometheus.bridgette.Bridgette._get_zones')
    @patch('Prometheus.bridgette.Bridgette._get_scenes')
    def test_assign_devices_zone_mapping(self, mock_scenes, mock_zones,
                                             mock_rooms, mock_lights, mock_light_data):
        """Test that devices are correctly mapped to zones (using light IDs)"""
        
        # Create mock lights 
        mock_light_2 = Mock(spec=HueLight)
        mock_light_2._dev_data = mock_light_data["light_2"] 
        mock_light_2.id = "light_id_2"
        mock_light_2.name = "office desk"
        
        mock_light_3 = Mock(spec=HueLight)
        mock_light_3._dev_data = mock_light_data["light_3"]
        mock_light_3.id = "light_id_3"
        mock_light_3.name = "zone light"
        
        mock_lights.return_value = {
            "light_id_2": mock_light_2,
            "light_id_3": mock_light_3
        }
        
        mock_zone = Mock(spec=HueZone)
        mock_zone.id = "zone_1"
        mock_zone.children = ["light_id_2", "light_id_3"]  # Light IDs directly
        mock_zone.devices = {}
        
        mock_rooms.return_value = {}
        mock_zone.name = "office zone"
        mock_zones.return_value = {"zone_1": mock_zone}
        mock_scenes.return_value = []
        
        mock_config = {'hostname': 'test_host', 'key': 'test_key'}
        with patch('builtins.open'), patch('yaml.load', return_value=mock_config), patch('pathlib.Path.exists', return_value=True):
            # Create bridge and trigger mapping
            bridge = Bridgette()
            
            # Verify zone mapping occurred correctly
            assert len(mock_zone.devices) == 2
            assert "office desk" in mock_zone.devices
            assert "zone light" in mock_zone.devices
            assert mock_zone.devices["office desk"] == mock_light_2
            assert mock_zone.devices["zone light"] == mock_light_3

    @patch('Prometheus.bridgette.Bridgette._get_lights')
    @patch('Prometheus.bridgette.Bridgette._get_rooms')
    @patch('Prometheus.bridgette.Bridgette._get_zones') 
    @patch('Prometheus.bridgette.Bridgette._get_scenes')
    def test_assign_devices_mixed_mapping(self, mock_scenes, mock_zones,
                                               mock_rooms, mock_lights, mock_light_data):
        """Test device mapping with both device IDs and light IDs in zones"""
        
        mock_light_1 = Mock(spec=HueLight)
        mock_light_1._dev_data = mock_light_data["light_1"]
        mock_light_1.id = "light_id_1"
        mock_light_1.name = "living room ceiling"
        
        mock_light_2 = Mock(spec=HueLight)
        mock_light_2._dev_data = mock_light_data["light_2"] 
        mock_light_2.id = "light_id_2"
        mock_light_2.name = "office desk"
        
        mock_lights.return_value = {
            "light_id_1": mock_light_1,
            "light_id_2": mock_light_2
        }
        
        # Zone with mixed ID types
        mock_zone = Mock(spec=HueZone)
        mock_zone.id = "zone_mixed"
        mock_zone.children = [
            "light_id_1",  # Direct light ID
            "device_2"     # Device ID (should match light_2's owner)
        ]
        mock_zone.devices = {}
        
        mock_rooms.return_value = {}
        mock_zone.name = "mixed zone"
        mock_zones.return_value = {"zone_mixed": mock_zone}
        mock_scenes.return_value = []
        
        mock_config = {'hostname': 'test_host', 'key': 'test_key'}
        with patch('builtins.open'), patch('yaml.load', return_value=mock_config), patch('pathlib.Path.exists', return_value=True):
            bridge = Bridgette()
            
            # Should handle both types correctly
            assert len(mock_zone.devices) == 2
            assert "living room ceiling" in mock_zone.devices  # Found by light ID
            assert "office desk" in mock_zone.devices  # Found by owner device ID


class TestDeviceUsage:
    """Tests for using devices functionality"""
    
    def test_device_control_access(self):
        """Test that devices can be accessed and controlled"""
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
                
                # Manually assign device (simulating bridge mapping)
                room.devices["test light"] = light
                
                # Test access and control
                assert "test light" in room.devices
                assert isinstance(room.devices["test light"], HueLight)
                assert room.devices["test light"].state == "True"
                
                # Test that we can call methods on devices
                with patch('Prometheus.device.HueResource._put') as mock_put:
                    room.devices["test light"].turn_off()
                    mock_put.assert_called_once()

    def test_empty_devices_handling(self):
        """Test behavior when rooms/zones have no devices"""
        room_data = {
            "id": "empty_room",
            "metadata": {"name": "Empty Room", "archetype": "living_room"}, 
            "children": [],  # No children
            "services": [{"rid": "grouped_light_1"}]
        }
        
        with patch('Prometheus.device.HueResource._get') as mock_get:
            mock_get.return_value = {"data": [{"on": {"on": False}}]}
            room = HueRoom(room_data, "test_host", "test_key")
            
            assert len(room.devices) == 0
            assert isinstance(room.devices, dict)
            
            # Should not raise errors when accessing empty dict
            assert "nonexistent" not in room.devices
            assert list(room.devices.keys()) == []


class TestDeviceIntegration:
    """Integration tests for devices with existing functionality"""
    
    def test_devices_docstring_updates(self):
        """Test that docstrings properly document devices"""
        # Check that HueRoom docstring mentions devices
        room_docstring = HueRoom.__doc__
        assert "devices" in room_docstring
        assert "Dictionary mapping light names to HueLight objects" in room_docstring
        
        # Check that HueZone docstring mentions devices  
        zone_docstring = HueZone.__doc__
        assert "devices" in zone_docstring
        assert "Dictionary mapping light names to HueLight objects" in zone_docstring

    def test_devices_backwards_compatibility(self):
        """Test that existing functionality still works with devices added"""
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
            assert hasattr(room, 'devices')
            
            # Existing methods should still work
            with patch('Prometheus.device.HueResource._put'):
                room.turn_off()  # Should not raise errors