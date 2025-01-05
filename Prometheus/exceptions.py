# exceptions.py
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