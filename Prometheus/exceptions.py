class HueError(Exception):
    """Base exception for Hue-related errors"""
    pass

class HueConnectionError(HueError):
    """Raised when there are network/connection issues"""
    pass

class HueResponseError(HueError):
    """Raised when the Hue Bridge returns an error response"""
    pass

class HueValidationError(HueError):
    """Raised when input validation fails"""
    pass


class BridgeError(Exception):
    """Base exception for all bridge-related errors."""
    pass

class BridgeConfigError(BridgeError):
    """Raised when there are issues with bridge configuration."""
    pass

class BridgeConnectionError(BridgeError):
    """Raised when there are problems connecting to the bridge."""
    pass

class BridgeResponseError(BridgeError):
    """Raised when the bridge returns unexpected or invalid data."""
    pass