class NotFoundException(Exception):
    """Exception raised when a requested resource is not found."""
    
    def __init__(self, message: str = "Resource not found"):
        self.message = message
        super().__init__(self.message)


class ConflictException(Exception):
    """Exception raised when an operation conflicts with existing state."""
    
    def __init__(self, message: str = "Conflict"):
        self.message = message
        super().__init__(self.message)


class InternalServerException(Exception):
    """Exception raised for internal server errors."""
    
    def __init__(self, message: str = "Internal server error"):
        self.message = message
        super().__init__(self.message)
