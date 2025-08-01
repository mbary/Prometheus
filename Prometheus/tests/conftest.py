"""Shared test fixtures for Prometheus test suite."""

import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.fixture
def hue_http():
    """
    Fixture providing mocked HTTP operations for Hue devices.
    
    Returns a namedtuple with mock_get and mock_put for patching
    HueResource HTTP operations.
    
    Usage:
        def test_something(hue_http):
            hue_http.mock_get.return_value = {"data": [{"on": {"on": True}}]}
            # Your test logic here
            hue_http.mock_put.assert_called_once_with(
                url="expected_url",
                headers=expected_headers,
                body=expected_body
            )
    """
    with patch('Prometheus.device.HueResource._get') as mock_get, \
         patch('Prometheus.device.HueResource._put') as mock_put:
        
        # Default mock responses
        mock_get.return_value = {"data": [{"on": {"on": True}}]}
        mock_put.return_value = None
        
        # Create a simple namespace object
        class HttpMocks:
            def __init__(self, get_mock, put_mock):
                self.mock_get = get_mock
                self.mock_put = put_mock
                
        yield HttpMocks(mock_get, mock_put)


@pytest.fixture  
def hue_http_with_session():
    """
    Alternative fixture that also mocks the HTTP session for integration tests.
    
    Useful for bridgette tests that need to mock requests.Session operations.
    """
    with patch('Prometheus.device.HueResource._get') as mock_get, \
         patch('Prometheus.device.HueResource._put') as mock_put, \
         patch('requests.Session.get') as mock_session_get, \
         patch('requests.Session.put') as mock_session_put:
        
        # Default mock responses
        mock_get.return_value = {"data": [{"on": {"on": True}}]}
        mock_put.return_value = None
        
        # Default session responses
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        mock_session_get.return_value = mock_response
        mock_session_put.return_value = mock_response
        
        class HttpMocksWithSession:
            def __init__(self, get_mock, put_mock, session_get_mock, session_put_mock):
                self.mock_get = get_mock
                self.mock_put = put_mock
                self.mock_session_get = session_get_mock
                self.mock_session_put = session_put_mock
                
        yield HttpMocksWithSession(mock_get, mock_put, mock_session_get, mock_session_put)