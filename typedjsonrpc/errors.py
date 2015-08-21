#
# Copyright 2015 Palantir Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Error classes for typedjsonrpc."""
import traceback


class Error(Exception):
    """Base class for all errors.

    .. versionadded:: 0.1.0
    """
    code = 0
    message = None
    data = None

    def __init__(self, data=None):
        super(Error, self).__init__(self.code, self.message, data)
        self.data = data

    def as_error_object(self):
        """Turns the error into an error object.

        .. versionadded:: 0.1.0
        """
        return {
            "code": self.code,
            "message": self.message,
            "data": self.data
        }


class ParseError(Error):
    """Invalid JSON was received by the server / JSON could not be parsed.

    .. versionadded:: 0.1.0
    """
    code = -32700
    message = "Parse error"


class InvalidRequestError(Error):
    """The JSON sent is not a valid request object.

    .. versionadded:: 0.1.0
    """
    code = -32600
    message = "Invalid request"


class MethodNotFoundError(Error):
    """The method does not exist.

    .. versionadded:: 0.1.0
    """
    code = -32601
    message = "Method not found"


class InvalidParamsError(Error):
    """Invalid method parameter(s).

    .. versionadded:: 0.1.0
    """
    code = -32602
    message = "Invalid params"


class InternalError(Error):
    """Internal JSON-RPC error.

    .. versionadded:: 0.1.0
    """
    code = -32603
    message = "Internal error"

    @staticmethod
    def from_error(exc_info, json_encoder, debug_url=None):
        """Wraps another Exception in an InternalError.

        :param exc_info: The exception info for the wrapped exception
        :type exc_info: (type, object, traceback)
        :type json_encoder: json.JSONEncoder
        :type debug_url: str | None
        :rtype: InternalError

        .. versionadded:: 0.1.0
        .. versionchanged:: 0.2.0
            Stringifies non-JSON-serializable objects
        """
        exc = exc_info[1]
        data = exc.__dict__.copy()
        for key, value in data.items():
            try:
                json_encoder.encode(value)
            except TypeError:
                data[key] = repr(value)
        data["traceback"] = "".join(traceback.format_exception(*exc_info))
        if debug_url is not None:
            data["debug_url"] = debug_url
        return InternalError(data)


class ServerError(Error):
    """Something else went wrong.

    .. versionadded:: 0.1.0
    """
    code = -32000
    message = "Server error"


class InvalidReturnTypeError(Error):
    """Return type does not match expected type.

    .. versionadded:: 0.1.0
    """
    code = -32001
    message = "Invalid return type"
