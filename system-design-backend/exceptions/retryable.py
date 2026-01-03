class RetryableException(Exception):
    """Base class for retryable exceptions"""
    pass

class DatabaseTimeoutException(RetryableException):
    """Database operation timed out"""
    pass

class InjectedFailureException(RetryableException):
    """Artificially injected failure for testing"""
    pass

class RedisTimeoutException(RetryableException):
    """Redis operation timed out"""
    pass