class GoCardlessError(Exception):
    pass


class ClientError(GoCardlessException):
    """Thrown when there was an error processing the request"""
    pass


class SignatureError(GoCardlessException):
    pass

