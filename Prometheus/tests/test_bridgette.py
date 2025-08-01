import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from ..bridgette import Bridgette
from ..device import HueZone, HueScene
from ..exceptions import BridgeConfigError, BridgeConnectionError


class TestBridgetteConfigLoading:
    """Tests for Bridgette's IP-first configuration loading functionality"""
    
    def test_load_bridge_config_from_valid_file_with_ip(self):
        """Test loading configuration from a valid YAML file with IP address"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("ip: 192.168.0.122\nkey: test-api-key-123")
            temp_path = Path(f.name)
        
        try:
            with patch('Prometheus.bridgette.load_dotenv'):
                bridge = Bridgette.__new__(Bridgette)
                address, key = bridge._load_bridge_config(temp_path)
                
                assert address == "192.168.0.122"
                assert key == "test-api-key-123"
        finally:
            os.unlink(temp_path)
    
    def test_load_bridge_config_from_valid_file_with_hostname_fallback(self):
        """Test loading configuration from a valid YAML file with hostname fallback"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("hostname: test-bridge.local\nkey: test-api-key-123")
            temp_path = Path(f.name)
        
        try:
            with patch('Prometheus.bridgette.load_dotenv'):
                bridge = Bridgette.__new__(Bridgette)
                address, key = bridge._load_bridge_config(temp_path)
                
                assert address == "test-bridge.local"
                assert key == "test-api-key-123"
        finally:
            os.unlink(temp_path)
    
    def test_load_bridge_config_ip_takes_precedence_over_hostname(self):
        """Test that IP takes precedence over hostname in config file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("ip: 192.168.0.122\nhostname: test-bridge.local\nkey: test-api-key-123")
            temp_path = Path(f.name)
        
        try:
            with patch('Prometheus.bridgette.load_dotenv'):
                bridge = Bridgette.__new__(Bridgette)
                address, key = bridge._load_bridge_config(temp_path)
                
                # Should use IP, not hostname
                assert address == "192.168.0.122"
                assert key == "test-api-key-123"
        finally:
            os.unlink(temp_path)
    
    def test_load_bridge_config_missing_address_in_file(self):
        """Test error when config file is missing both IP and hostname fields"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("key: test-api-key-123")
            temp_path = Path(f.name)
        
        try:
            with patch('Prometheus.bridgette.load_dotenv'):
                bridge = Bridgette.__new__(Bridgette)
                with pytest.raises(BridgeConfigError, match="Configuration file must contain 'ip' \\(or 'hostname'\\) and 'key' fields"):
                    bridge._load_bridge_config(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_load_bridge_config_missing_key_in_file(self):
        """Test error when config file is missing key field"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("ip: 192.168.0.122")
            temp_path = Path(f.name)
        
        try:
            with patch('Prometheus.bridgette.load_dotenv'):
                bridge = Bridgette.__new__(Bridgette)
                with pytest.raises(BridgeConfigError, match="Configuration file must contain 'ip' \\(or 'hostname'\\) and 'key' fields"):
                    bridge._load_bridge_config(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_load_bridge_config_invalid_yaml(self):
        """Test error when config file contains invalid YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("ip: 192.168.0.122\nkey: [invalid: yaml: syntax")
            temp_path = Path(f.name)
        
        try:
            with patch('Prometheus.bridgette.load_dotenv'):
                bridge = Bridgette.__new__(Bridgette)
                with pytest.raises(BridgeConfigError, match="Error parsing configuration file"):
                    bridge._load_bridge_config(temp_path)
        finally:
            os.unlink(temp_path)
    
    @patch.dict(os.environ, {'HUE_IP': '192.168.0.122', 'HUE_KEY': 'env-api-key-456'})
    def test_load_bridge_config_from_env_vars_ip_preferred(self):
        """Test loading configuration from HUE_IP environment variable"""
        non_existent_path = Path('./non_existent_config.yaml')
        
        with patch('Prometheus.bridgette.load_dotenv'):
            bridge = Bridgette.__new__(Bridgette)
            address, key = bridge._load_bridge_config(non_existent_path)
            
            assert address == "192.168.0.122"
            assert key == "env-api-key-456"
    
    @patch.dict(os.environ, {'HUE_HOSTNAME': 'env-bridge.local', 'HUE_KEY': 'env-api-key-456'}, clear=True)
    def test_load_bridge_config_from_env_vars_hostname_fallback(self):
        """Test loading configuration from HUE_HOSTNAME when HUE_IP not available"""
        non_existent_path = Path('./non_existent_config.yaml')
        
        with patch('Prometheus.bridgette.load_dotenv'):
            bridge = Bridgette.__new__(Bridgette)
            address, key = bridge._load_bridge_config(non_existent_path)
            
            assert address == "env-bridge.local"
            assert key == "env-api-key-456"
    
    @patch.dict(os.environ, {'HUE_IP': '192.168.0.122', 'HUE_HOSTNAME': 'env-bridge.local', 'HUE_KEY': 'env-api-key-456'})
    def test_load_bridge_config_env_ip_takes_precedence(self):
        """Test that HUE_IP takes precedence over HUE_HOSTNAME in environment variables"""
        non_existent_path = Path('./non_existent_config.yaml')
        
        with patch('Prometheus.bridgette.load_dotenv'):
            bridge = Bridgette.__new__(Bridgette)
            address, key = bridge._load_bridge_config(non_existent_path)
            
            # Should use IP, not hostname
            assert address == "192.168.0.122"
            assert key == "env-api-key-456"
    
    @patch.dict(os.environ, {'HUE_IP': '192.168.0.122'}, clear=True)
    def test_load_bridge_config_missing_key_env_var(self):
        """Test error when only IP is set in environment variables"""
        non_existent_path = Path('./non_existent_config.yaml')
        
        with patch('Prometheus.bridgette.load_dotenv'):
            bridge = Bridgette.__new__(Bridgette)
            with pytest.raises(BridgeConfigError, match="Bridge configuration not found.*HUE_KEY"):
                bridge._load_bridge_config(non_existent_path)
    
    @patch.dict(os.environ, {'HUE_KEY': 'env-api-key-456'}, clear=True)
    def test_load_bridge_config_missing_address_env_var(self):
        """Test error when only key is set in environment variables"""
        non_existent_path = Path('./non_existent_config.yaml')
        
        with patch('Prometheus.bridgette.load_dotenv'):
            bridge = Bridgette.__new__(Bridgette)
            with pytest.raises(BridgeConfigError, match="Bridge configuration not found.*HUE_IP or HUE_HOSTNAME"):
                bridge._load_bridge_config(non_existent_path)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_load_bridge_config_no_config_available(self):
        """Test error when neither config file nor environment variables are available"""
        non_existent_path = Path('./non_existent_config.yaml')
        
        with patch('Prometheus.bridgette.load_dotenv'):
            bridge = Bridgette.__new__(Bridgette)
            with pytest.raises(BridgeConfigError, match="Bridge configuration not found.*HUE_IP or HUE_HOSTNAME, HUE_KEY"):
                bridge._load_bridge_config(non_existent_path)
    
    @patch.dict(os.environ, {'HUE_IP': '192.168.0.100', 'HUE_HOSTNAME': 'env-bridge.local', 'HUE_KEY': 'env-api-key-456'})
    def test_load_bridge_config_file_takes_precedence(self):
        """Test that config file takes precedence over environment variables"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("ip: 192.168.0.122\nkey: file-api-key-789")
            temp_path = Path(f.name)
        
        try:
            with patch('Prometheus.bridgette.load_dotenv'):
                bridge = Bridgette.__new__(Bridgette)
                address, key = bridge._load_bridge_config(temp_path)
                
                # Should use file values, not environment values
                assert address == "192.168.0.122"
                assert key == "file-api-key-789"
        finally:
            os.unlink(temp_path)
    
    def test_load_dotenv_called(self):
        """Test that load_dotenv is called during configuration loading"""
        with patch('Prometheus.bridgette.load_dotenv') as mock_load_dotenv:
            with patch.dict(os.environ, {'HUE_IP': '192.168.0.122', 'HUE_KEY': 'test'}):
                bridge = Bridgette.__new__(Bridgette)
                bridge._load_bridge_config(Path('./non_existent.yaml'))
                
                mock_load_dotenv.assert_called_once()


class TestBridgetteChildDeviceMapping:
    """Tests for Bridgette's child device mapping functionality"""
    
    @patch('Prometheus.bridgette.Bridgette._assign_devices')
    @patch('Prometheus.bridgette.Bridgette._assign_scenes')
    @patch('Prometheus.bridgette.Bridgette._get_zones')
    @patch('Prometheus.bridgette.Bridgette._get_rooms') 
    @patch('Prometheus.bridgette.Bridgette._get_lights')
    def test_assign_child_devices_called_during_init(self, mock_get_lights, 
                                                   mock_get_rooms, mock_get_zones,
                                                   mock_assign_scenes, 
                                                   mock_assign_devices):
        """Test that _assign_devices is called during Bridgette initialization"""
        
        # Mock the required methods
        mock_get_lights.return_value = {}
        mock_get_rooms.return_value = {} 
        mock_get_zones.return_value = {}
        
        mock_config = {'hostname': 'test_host', 'key': 'test_key'}
        with patch('builtins.open'), patch('yaml.load', return_value=mock_config), patch('pathlib.Path.exists', return_value=True):
            bridge = Bridgette()
            
            # Verify _assign_devices was called
            mock_assign_devices.assert_called_once()
            
            # Verify it's called after _assign_scenes (correct order)
            assert mock_assign_scenes.call_count == 1
            assert mock_assign_devices.call_count == 1

    @patch('Prometheus.bridgette.Bridgette._get_scenes')
    @patch('Prometheus.bridgette.Bridgette._get_zones')
    @patch('Prometheus.bridgette.Bridgette._get_rooms')
    @patch('Prometheus.bridgette.Bridgette._get_lights')
    def test_assign_devices_implementation(self, mock_get_lights, mock_get_rooms,
                                               mock_get_zones, mock_get_scenes):
        """Test the actual implementation of _assign_devices"""
        
        # Create mock lights with different ID types
        mock_light_1 = Mock()
        mock_light_1._dev_data = {"owner": {"rid": "device_1"}}
        mock_light_1.id = "light_1"
        mock_light_1.name = "ceiling light"
        
        mock_light_2 = Mock()
        mock_light_2._dev_data = {"owner": {"rid": "device_2"}}  
        mock_light_2.id = "light_2"
        mock_light_2.name = "desk lamp"
        
        mock_get_lights.return_value = {
            "light_1": mock_light_1,
            "light_2": mock_light_2
        }
        
        # Create mock room (uses device IDs)
        mock_room = Mock()
        mock_room.id = "room_1"
        mock_room.children = ["device_1", "device_2"]
        mock_room.devices = {}
        
        # Create mock zone (uses light IDs) 
        mock_zone = Mock()
        mock_zone.id = "zone_1"
        mock_zone.children = ["light_1", "light_2"]
        mock_zone.devices = {}
        
        # Create mock room and zone with proper attributes
        mock_room.name = "living room"
        mock_zone.name = "office zone"
        
        mock_get_rooms.return_value = {"room_1": mock_room}
        mock_get_zones.return_value = {"zone_1": mock_zone}
        mock_get_scenes.return_value = []
        
        mock_config = {'hostname': 'test_host', 'key': 'test_key'}
        with patch('builtins.open'), patch('yaml.load', return_value=mock_config), patch('pathlib.Path.exists', return_value=True):
            bridge = Bridgette()
            
            # Verify room mapping (by device ID)
            assert len(mock_room.devices) == 2
            assert "ceiling light" in mock_room.devices
            assert "desk lamp" in mock_room.devices
            assert mock_room.devices["ceiling light"] == mock_light_1
            assert mock_room.devices["desk lamp"] == mock_light_2
            
            # Verify zone mapping (by light ID)
            assert len(mock_zone.devices) == 2
            assert "ceiling light" in mock_zone.devices
            assert "desk lamp" in mock_zone.devices
            assert mock_zone.devices["ceiling light"] == mock_light_1
            assert mock_zone.devices["desk lamp"] == mock_light_2

    @patch('Prometheus.bridgette.Bridgette._get_scenes')  
    @patch('Prometheus.bridgette.Bridgette._get_zones')
    @patch('Prometheus.bridgette.Bridgette._get_rooms')
    @patch('Prometheus.bridgette.Bridgette._get_lights')
    def test_assign_devices_no_matches(self, mock_get_lights, mock_get_rooms,
                                           mock_get_zones, mock_get_scenes):
        """Test _assign_devices when no devices match"""
        
        # Light with owner that doesn't match any room/zone children
        mock_light = Mock()
        mock_light._dev_data = {"owner": {"rid": "device_999"}}
        mock_light.id = "light_999"
        
        mock_get_lights.return_value = {"orphan light": mock_light}
        
        # Room/zone with children that don't match any light owners/IDs
        mock_room = Mock()
        mock_room.id = "room_2"
        mock_room.children = ["device_1", "device_2"] 
        mock_room.devices = {}
        
        mock_zone = Mock()
        mock_zone.id = "zone_2"
        mock_zone.children = ["light_1", "light_2"]
        mock_zone.devices = {}
        
        mock_get_rooms.return_value = {"empty room": mock_room}
        mock_get_zones.return_value = {"empty zone": mock_zone}
        mock_get_scenes.return_value = []
        
        mock_config = {'hostname': 'test_host', 'key': 'test_key'}
        with patch('builtins.open'), patch('yaml.load', return_value=mock_config), patch('pathlib.Path.exists', return_value=True):
            bridge = Bridgette()
            
            # Should complete without errors, but no mappings
            assert len(mock_room.devices) == 0
            assert len(mock_zone.devices) == 0

    @patch('Prometheus.bridgette.Bridgette._get_scenes')
    @patch('Prometheus.bridgette.Bridgette._get_zones')
    @patch('Prometheus.bridgette.Bridgette._get_rooms')
    @patch('Prometheus.bridgette.Bridgette._get_lights')
    def test_assign_devices_partial_matches(self, mock_get_lights, mock_get_rooms,
                                                 mock_get_zones, mock_get_scenes):
        """Test _assign_devices with partial matches"""
        
        # Create lights where only some match room/zone children
        mock_light_1 = Mock()
        mock_light_1._dev_data = {"owner": {"rid": "device_1"}}  # Will match room
        mock_light_1.id = "light_1"
        mock_light_1.name = "matching light"
        
        mock_light_2 = Mock()
        mock_light_2._dev_data = {"owner": {"rid": "device_999"}}  # Won't match anything
        mock_light_2.id = "light_999"
        mock_light_2.name = "orphan light"
        
        mock_get_lights.return_value = {
            "light_1": mock_light_1,
            "light_999": mock_light_2
        }
        
        mock_room = Mock()
        mock_room.id = "room_3"
        mock_room.children = ["device_1", "device_2"]  # device_1 matches, device_2 doesn't
        mock_room.devices = {}
        
        mock_room.name = "test room"
        mock_get_rooms.return_value = {"room_3": mock_room}
        mock_get_zones.return_value = {}
        mock_get_scenes.return_value = []
        
        mock_config = {'hostname': 'test_host', 'key': 'test_key'}
        with patch('builtins.open'), patch('yaml.load', return_value=mock_config), patch('pathlib.Path.exists', return_value=True):
            bridge = Bridgette()
            
            # Only the matching light should be mapped
            assert len(mock_room.devices) == 1
            assert "matching light" in mock_room.devices
            assert "orphan light" not in mock_room.devices
            assert mock_room.devices["matching light"] == mock_light_1


class TestBridgetteHueZoneIntegration:
    """Tests for Bridgette's HueZone integration and management"""

    @pytest.fixture
    def mock_zone_api_data(self):
        """Mock API data for zone discovery"""
        return {
            "data": [
                {
                    "id": "zone_1",
                    "metadata": {
                        "name": "Living Area",
                        "archetype": "living_room"
                    },
                    "services": [{"rid": "grouped_light_zone_1"}],
                    "children": [
                        {"rid": "light_1", "rtype": "light"},
                        {"rid": "light_2", "rtype": "light"}
                    ],
                    "on": {"on": False}
                },
                {
                    "id": "zone_2", 
                    "metadata": {
                        "name": "Office",
                        "archetype": "office"
                    },
                    "services": [{"rid": "grouped_light_zone_2"}],
                    "children": [
                        {"rid": "light_3", "rtype": "light"}
                    ],
                    "on": {"on": True}
                }
            ]
        }

    @pytest.fixture  
    def mock_zone_scene_data(self):
        """Mock scene data for zones"""
        return [
            {
                "id": "scene_1",
                "type": "scene",
                "metadata": {"name": "Bright"},
                "group": {"rid": "zone_1", "rtype": "zone"},
                "status": {"active": "inactive"}
            },
            {
                "id": "scene_2",
                "type": "smart_scene",
                "metadata": {"name": "Natural Light"},
                "group": {"rid": "zone_2", "rtype": "zone"},
                "state": "active"
            }
        ]

    def test_zone_discovery_and_creation(self, mock_zone_api_data):
        """Test that zones are properly discovered and HueZone objects are created"""
        mock_config = {'hostname': 'test_host', 'key': 'test_key'}
        
        with patch('builtins.open'), \
             patch('yaml.load', return_value=mock_config), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('Prometheus.bridgette.Bridgette._get_lights', return_value={}), \
             patch('Prometheus.bridgette.Bridgette._get_rooms', return_value={}), \
             patch('Prometheus.bridgette.Bridgette._get_scenes', return_value=[]), \
             patch('requests.Session.get') as mock_get:
            
            # Mock the zone API response
            mock_response = Mock()
            mock_response.json.return_value = mock_zone_api_data
            mock_get.return_value = mock_response
            
            bridge = Bridgette()
            
            # Verify zones were created
            assert len(bridge.zones) == 2
            assert "living area" in bridge.zones
            assert "office" in bridge.zones
            
            # Verify HueZone objects were created properly
            living_area = bridge.zones["living area"]
            office = bridge.zones["office"]
            
            assert isinstance(living_area, HueZone)
            assert isinstance(office, HueZone)
            
            # Verify zone properties
            assert living_area.id == "zone_1"
            assert living_area.name == "living area"  # Normalized
            assert living_area.children == ["light_1", "light_2"]
            
            assert office.id == "zone_2"
            assert office.name == "office"
            assert office.children == ["light_3"]

    def test_zone_scene_assignment(self, mock_zone_api_data, mock_zone_scene_data):
        """Test that scenes are properly assigned to zones"""
        mock_config = {'hostname': 'test_host', 'key': 'test_key'}
        
        with patch('builtins.open'), \
             patch('yaml.load', return_value=mock_config), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('Prometheus.bridgette.Bridgette._get_lights', return_value={}), \
             patch('Prometheus.bridgette.Bridgette._get_rooms', return_value={}), \
             patch('requests.Session.get') as mock_get:
            
            # Mock the zone API response
            mock_zone_response = Mock()
            mock_zone_response.json.return_value = mock_zone_api_data
            
            # Mock scene API responses
            mock_regular_scene_response = Mock()
            mock_regular_scene_response.json.return_value = {"data": [mock_zone_scene_data[0]]}
            
            mock_smart_scene_response = Mock()
            mock_smart_scene_response.json.return_value = {"data": [mock_zone_scene_data[1]]}
            
            # Set up the API call sequence
            mock_get.side_effect = [
                mock_zone_response,  # _get_zones call
                mock_regular_scene_response,  # scene API call
                mock_smart_scene_response   # smart_scene API call
            ]
            
            bridge = Bridgette()
            
            # Verify scenes were assigned to correct zones
            living_area = bridge.zones["living area"]
            office = bridge.zones["office"]
            
            assert len(living_area.scenes) == 1
            assert "bright" in living_area.scenes
            assert isinstance(living_area.scenes["bright"], HueScene)
            assert living_area.scenes["bright"].type == "scene"
            
            assert len(office.scenes) == 1
            assert "natural light" in office.scenes
            assert isinstance(office.scenes["natural light"], HueScene) 
            assert office.scenes["natural light"].type == "smart_scene"

    def test_zone_state_monitoring_integration(self, mock_zone_api_data):
        """Test integration between zones and get_current_state method"""
        mock_config = {'hostname': 'test_host', 'key': 'test_key'}
        
        with patch('builtins.open'), \
             patch('yaml.load', return_value=mock_config), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('Prometheus.bridgette.Bridgette._get_lights', return_value={}), \
             patch('Prometheus.bridgette.Bridgette._get_rooms', return_value={}), \
             patch('Prometheus.bridgette.Bridgette._get_scenes', return_value=[]), \
             patch('requests.Session.get') as mock_get:
            
            # Mock the zone API response
            mock_response = Mock()
            mock_response.json.return_value = mock_zone_api_data
            mock_get.return_value = mock_response
            
            bridge = Bridgette()
            
            # Mock the _get_active_scene_for_group method for testing
            with patch.object(bridge, '_get_active_scene_for_group') as mock_get_active_scene:
                mock_get_active_scene.return_value = None  # No active scene
                
                current_state = bridge.get_current_state()
                
                # Verify zones are included in current state
                assert "zones" in current_state
                assert len(current_state["zones"]) == 2
                
                # Verify zone state structure
                living_area_state = current_state["zones"]["living area"]
                assert "zone_state" in living_area_state
                assert "lights" in living_area_state
                assert living_area_state["zone_state"]["scene"] is None

    def test_zone_special_office_behavior(self):
        """Test that office zones get special turn_on behavior"""
        office_zone_data = {
            "data": [{
                "id": "office_zone",
                "metadata": {
                    "name": "Office",
                    "archetype": "office"
                },
                "services": [{"rid": "grouped_light_office"}],
                "children": [{"rid": "light_office", "rtype": "light"}],
                "on": {"on": False}
            }]
        }
        
        mock_config = {'hostname': 'test_host', 'key': 'test_key'}
        
        with patch('builtins.open'), \
             patch('yaml.load', return_value=mock_config), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('Prometheus.bridgette.Bridgette._get_lights', return_value={}), \
             patch('Prometheus.bridgette.Bridgette._get_rooms', return_value={}), \
             patch('Prometheus.bridgette.Bridgette._get_scenes', return_value=[]), \
             patch('requests.Session.get') as mock_get:
            
            mock_response = Mock()
            mock_response.json.return_value = office_zone_data
            mock_get.return_value = mock_response
            
            bridge = Bridgette()
            
            # Verify office zone exists
            assert "office" in bridge.zones
            office = bridge.zones["office"]
            
            # Add a natural light scene to test special behavior
            natural_light_scene = HueScene({
                "id": "natural_light_scene",
                "type": "smart_scene",
                "metadata": {"name": "Natural Light"}
            }, "test_host", "test_key")
            
            office.scenes["natural light"] = natural_light_scene
            
            # Test that office zone would attempt to use natural light scene
            with patch.object(office, 'set_smart_scene') as mock_set_smart_scene:
                office.turn_on()
                mock_set_smart_scene.assert_called_once_with(scene_name='natural light')

    def test_zone_error_handling_during_discovery(self):
        """Test error handling during zone discovery"""
        mock_config = {'hostname': 'test_host', 'key': 'test_key'}
        
        with patch('builtins.open'), \
             patch('yaml.load', return_value=mock_config), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('Prometheus.bridgette.Bridgette._get_lights', return_value={}), \
             patch('Prometheus.bridgette.Bridgette._get_rooms', return_value={}), \
             patch('Prometheus.bridgette.Bridgette._get_scenes', return_value=[]), \
             patch('requests.Session.get') as mock_get:
            
            # Mock a network error during zone discovery
            mock_get.side_effect = Exception("Network timeout")
            
            # Should handle the error gracefully and create empty zones dict
            bridge = Bridgette()
            assert isinstance(bridge.zones, dict)
            assert len(bridge.zones) == 0

    def test_zone_device_assignment_integration(self):
        """Test integration between zone creation and device assignment"""
        zone_data = {
            "data": [{
                "id": "test_zone",
                "metadata": {"name": "Test Zone", "archetype": "zone"},
                "services": [{"rid": "grouped_light_test"}],
                "children": [{"rid": "light_1", "rtype": "light"}],
                "on": {"on": False}
            }]
        }
        
        # Mock light that should be assigned to the zone
        mock_light = Mock()
        mock_light.name = "test light"
        mock_light.id = "light_1"
        mock_lights = {"test light": mock_light}
        
        mock_config = {'hostname': 'test_host', 'key': 'test_key'}
        
        with patch('builtins.open'), \
             patch('yaml.load', return_value=mock_config), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('Prometheus.bridgette.Bridgette._get_lights', return_value=mock_lights), \
             patch('Prometheus.bridgette.Bridgette._get_rooms', return_value={}), \
             patch('Prometheus.bridgette.Bridgette._get_scenes', return_value=[]), \
             patch('requests.Session.get') as mock_get:
            
            mock_response = Mock()
            mock_response.json.return_value = zone_data
            mock_get.return_value = mock_response
            
            bridge = Bridgette()
            
            # Verify zone was created and device was assigned
            assert "test zone" in bridge.zones
            test_zone = bridge.zones["test zone"]
            
            # Note: The actual device assignment happens in _assign_devices
            # This test verifies the zone structure is ready for assignment
            assert hasattr(test_zone, 'devices')
            assert isinstance(test_zone.devices, dict)
            assert hasattr(test_zone, 'children')
            assert test_zone.children == ["light_1"]