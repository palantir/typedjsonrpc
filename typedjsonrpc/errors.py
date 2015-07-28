"""This module defines error classes for typedjsonrpc."""


class Error(Exception):
    """Base class for all errors."""
    code = 0
    message = None
    data = None

    def __init__(self, data=None):
        super(Error, self).__init__(self.code, self.message, data)
        self.data = data

    def as_error_object(self):
        """Turns the error into an error object."""
        return {
            "code": self.code,
            "message": self.message,
            "data": self.data
        }


class ParseError(Error):
    """Invalid JSON was received by the server / JSON could not be parsed."""
    code = -32700
    message = "Parse error"


class InvalidRequestError(Error):
    """The JSON sent is not a valid request object."""
    code = -32600
    message = "Invalid request"


class MethodNotFoundError(Error):
    """The method does not exist."""
    code = -32601
    message = "Method not found"


class InvalidParamsError(Error):
    """Invalid method parameter(s)."""
    code = -32602
    message = "Invalid params"


class InternalError(Error):
    """Internal JSON-RPC error."""
    code = -32603
    message = "Internal error"


class ServerError(Error):
    """Something else went wrong."""
    code = -32000
    message = "Server error"
