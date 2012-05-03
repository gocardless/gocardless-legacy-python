class GoCardlessError(Exception):
    pass


class ClientError(GoCardlessError):
    """Thrown when there was an error processing the request"""
    pass


class SignatureError(GoCardlessError):
    pass

