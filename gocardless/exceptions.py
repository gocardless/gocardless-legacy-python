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
        if type(errors) == list:
            msgs += errors
        elif type(errors) == dict:
            for field in errors:
                msgs += map(lambda m: "{f} {m}".format(f=field, m=m),
                            errors[field])
        else:
            msgs = [str(errors)]
        return ", ".join(msgs)


class SignatureError(GoCardlessError):
    pass

