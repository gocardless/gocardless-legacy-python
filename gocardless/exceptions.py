class GoCardlessError(Exception):
    pass


class ClientError(GoCardlessError):
    """Thrown when there was an error processing the request"""
    def __init__(self, message, errors=None):
        self.message = message
        if errors is not None:
            self.message += self._stringify_errors(errors)

    def _stringify_errors(self, errors):
        msgs = []
        if isinstance(errors, list):
            msgs += errors
        elif isinstance(errors, dict):
            for field in errors:
                msgs += ['{} {}'.format(field, msg) for msg in errors[field]]
        else:
            msgs = [str(errors)]
        return ", ".join(msgs)


class SignatureError(GoCardlessError):
    pass

