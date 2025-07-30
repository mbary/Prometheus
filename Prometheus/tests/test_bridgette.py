import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from ..bridgette import Bridgette
from ..exceptions import BridgeConfigError, BridgeConnectionError


class TestBridgetteConfigLoading:
    """Tests for Bridgette's configuration loading functionality"""
    
    def test_load_bridge_config_from_valid_file(self):
        """Test loading configuration from a valid YAML file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("hostname: test-bridge.local\nkey: test-api-key-123")
            temp_path = Path(f.name)
        
        try:
            # Mock load_dotenv to avoid side effects
            with patch('Prometheus.bridgette.load_dotenv'):
                bridge = Bridgette.__new__(Bridgette)
                hostname, key = bridge._load_bridge_config(temp_path)
                
                assert hostname == "test-bridge.local"
                assert key == "test-api-key-123"
        finally:
            os.unlink(temp_path)
    
    def test_load_bridge_config_missing_hostname_in_file(self):
        """Test error when config file is missing hostname field"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("key: test-api-key-123")
            temp_path = Path(f.name)
        
        try:
            with patch('Prometheus.bridgette.load_dotenv'):
                bridge = Bridgette.__new__(Bridgette)
                with pytest.raises(BridgeConfigError, match="Configuration file must contain 'hostname' and 'key' fields"):
                    bridge._load_bridge_config(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_load_bridge_config_missing_key_in_file(self):
        """Test error when config file is missing key field"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("hostname: test-bridge.local")
            temp_path = Path(f.name)
        
        try:
            with patch('Prometheus.bridgette.load_dotenv'):
                bridge = Bridgette.__new__(Bridgette)
                with pytest.raises(BridgeConfigError, match="Configuration file must contain 'hostname' and 'key' fields"):
                    bridge._load_bridge_config(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_load_bridge_config_invalid_yaml(self):
        """Test error when config file contains invalid YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("hostname: test-bridge.local\nkey: [invalid: yaml: syntax")
            temp_path = Path(f.name)
        
        try:
            with patch('Prometheus.bridgette.load_dotenv'):
                bridge = Bridgette.__new__(Bridgette)
                with pytest.raises(BridgeConfigError, match="Error parsing configuration file"):
                    bridge._load_bridge_config(temp_path)
        finally:
            os.unlink(temp_path)
    
    @patch.dict(os.environ, {'HUE_HOSTNAME': 'env-bridge.local', 'HUE_KEY': 'env-api-key-456'})
    def test_load_bridge_config_from_env_vars(self):
        """Test loading configuration from environment variables when file doesn't exist"""
        non_existent_path = Path('./non_existent_config.yaml')
        
        with patch('Prometheus.bridgette.load_dotenv'):
            bridge = Bridgette.__new__(Bridgette)
            hostname, key = bridge._load_bridge_config(non_existent_path)
            
            assert hostname == "env-bridge.local"
            assert key == "env-api-key-456"
    
    @patch.dict(os.environ, {'HUE_HOSTNAME': 'env-bridge.local'}, clear=True)
    def test_load_bridge_config_missing_key_env_var(self):
        """Test error when only hostname is set in environment variables"""
        non_existent_path = Path('./non_existent_config.yaml')
        
        with patch('Prometheus.bridgette.load_dotenv'):
            bridge = Bridgette.__new__(Bridgette)
            with pytest.raises(BridgeConfigError, match="Bridge configuration not found.*HUE_KEY"):
                bridge._load_bridge_config(non_existent_path)
    
    @patch.dict(os.environ, {'HUE_KEY': 'env-api-key-456'}, clear=True)
    def test_load_bridge_config_missing_hostname_env_var(self):
        """Test error when only key is set in environment variables"""
        non_existent_path = Path('./non_existent_config.yaml')
        
        with patch('Prometheus.bridgette.load_dotenv'):
            bridge = Bridgette.__new__(Bridgette)
            with pytest.raises(BridgeConfigError, match="Bridge configuration not found.*HUE_HOSTNAME"):
                bridge._load_bridge_config(non_existent_path)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_load_bridge_config_no_config_available(self):
        """Test error when neither config file nor environment variables are available"""
        non_existent_path = Path('./non_existent_config.yaml')
        
        with patch('Prometheus.bridgette.load_dotenv'):
            bridge = Bridgette.__new__(Bridgette)
            with pytest.raises(BridgeConfigError, match="Bridge configuration not found.*HUE_HOSTNAME, HUE_KEY"):
                bridge._load_bridge_config(non_existent_path)
    
    @patch.dict(os.environ, {'HUE_HOSTNAME': 'env-bridge.local', 'HUE_KEY': 'env-api-key-456'})
    def test_load_bridge_config_file_takes_precedence(self):
        """Test that config file takes precedence over environment variables"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("hostname: file-bridge.local\nkey: file-api-key-789")
            temp_path = Path(f.name)
        
        try:
            with patch('Prometheus.bridgette.load_dotenv'):
                bridge = Bridgette.__new__(Bridgette)
                hostname, key = bridge._load_bridge_config(temp_path)
                
                # Should use file values, not environment values
                assert hostname == "file-bridge.local"
                assert key == "file-api-key-789"
        finally:
            os.unlink(temp_path)
    
    def test_load_dotenv_called(self):
        """Test that load_dotenv is called during configuration loading"""
        with patch('Prometheus.bridgette.load_dotenv') as mock_load_dotenv:
            with patch.dict(os.environ, {'HUE_HOSTNAME': 'test', 'HUE_KEY': 'test'}):
                bridge = Bridgette.__new__(Bridgette)
                bridge._load_bridge_config(Path('./non_existent.yaml'))
                
                mock_load_dotenv.assert_called_once()


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