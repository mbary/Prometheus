import pytest
import requests
from unittest.mock import Mock, patch
from ..device import HueResource
from ..exceptions import HueConnectionError, HueValidationError, HueResponseError

@pytest.fixture
def valid_dev_dict():
    return {
        "id": "123",
        "metadata": {
            "name": "Test Device",
            "archetype": "light"
        }
    }

@pytest.fixture
def mock_session():
    session = Mock(spec=requests.Session)

    mock_response = Mock()
    mock_response.json.return_value = {"data": [{"state": "on"}]}
    session.get.return_value = mock_response
    return session

class TestHueResource:

    def test_initialisation_with_valid_data(self, valid_dev_dict, mock_session):
        hue_resource = HueResource(dev_dict=valid_dev_dict, hue_hostname="test", hue_key="test", http_client=mock_session)
        assert hue_resource.id == "123"
        assert hue_resource.name == "test device"
        assert hue_resource.dev_type == "light"


    def test_initialisation_with_invalid_data(self, valid_dev_dict, mock_session):
        invalid_dev_dict = {"metadata":{}}

        with pytest.raises(HueValidationError) as e:
            HueResource(dev_dict=invalid_dev_dict, hue_hostname="bridge.local", hue_key="invalid_key", http_client=mock_session)
            assert 'missing required fields' in str(e.value)


    def test_get_successful_request(self, valid_dev_dict, mock_session):
        """Test successful GET request"""
        resource = HueResource(
            dev_dict=valid_dev_dict,
            hue_hostname="bridge.local",
            hue_key="testkey",
            http_client=mock_session
        )
        
        result = resource._get("https://test.url")
        
        # Verify the request was made correctly
        mock_session.get.assert_called_once()
        assert result == {"data": [{"state": "on"}]}

    def test_get_network_error(self, valid_dev_dict, mock_session):
        """Test GET request with network error"""
        mock_session.get.side_effect = requests.exceptions.ConnectionError(
            "Network error"
        )
        
        resource = HueResource(
            dev_dict=valid_dev_dict,
            hue_hostname="bridge.local",
            hue_key="testkey",
            http_client=mock_session
        )
        
        with pytest.raises(HueConnectionError) as exc_info:
            resource._get("https://test.url")
        assert "Network error" in str(exc_info.value) 


    def test_put_successful_update(self, valid_dev_dict, mock_session):
        """Test successful PUT request"""
        # Configure mock to simulate successful update
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = ""  # Successful PUTs often return empty response
        mock_session.put.return_value = mock_response
        
        resource = HueResource(
            dev_dict=valid_dev_dict,
            hue_hostname="bridge.local",
            hue_key="testkey",
            http_client=mock_session
        )
        
        # Should not raise any exceptions
        resource._put(
            "https://test.url",
            headers={"Content-Type": "application/json"},
            body={"on": {"on": True}}
        )
        
        # Verify request was made correctly
        mock_session.put.assert_called_once()

    def test_put_empty_body(self, valid_dev_dict, mock_session):
        """Test PUT with empty body"""
        resource = HueResource(
            dev_dict=valid_dev_dict,
            hue_hostname="bridge.local",
            hue_key="testkey",
            http_client=mock_session
        )
        
        with pytest.raises(HueValidationError) as exc_info:
            resource._put("https://test.url", headers={}, body={})
        assert "requires a body" in str(exc_info.value)

    def test_put_bridge_error(self, valid_dev_dict, mock_session):
        """Test PUT where bridge returns an error"""
        # Configure mock to simulate bridge error response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"errors": ["Invalid state"]}'
        mock_response.json.return_value = {"errors": ["Invalid state"]}
        mock_session.put.return_value = mock_response
        
        resource = HueResource(
            dev_dict=valid_dev_dict,
            hue_hostname="bridge.local",
            hue_key="testkey",
            http_client=mock_session
        )
        
        with pytest.raises(HueResponseError) as exc_info:
            resource._put(
                "https://test.url",
                headers={"Content-Type": "application/json"},
                body={"on": {"on": True}}
            )
        assert "Failed to update device state" in str(exc_info.value)

    def test_put_network_error(self, valid_dev_dict, mock_session):
        """Test PUT with network failure"""
        mock_session.put.side_effect = requests.exceptions.ConnectionError(
            "Network error"
        )
        
        resource = HueResource(
            dev_dict=valid_dev_dict,
            hue_hostname="bridge.local",
            hue_key="testkey",
            http_client=mock_session
        )
        
        with pytest.raises(HueConnectionError) as exc_info:
            resource._put(
                "https://test.url",
                headers={"Content-Type": "application/json"},
                body={"on": {"on": True}}
            )
        assert "Network error" in str(exc_info.value)