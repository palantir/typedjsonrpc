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
import sys


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

    @staticmethod
    def from_error(exc, debug_url=None):
        """Wraps another Exception in an InternalError.

        :type exc: Exception
        :rtype: InternalError
        """
        data = exc.__dict__.copy()
        data["traceback"] = "".join(traceback.format_exception(*sys.exc_info()))
        if debug_url is not None:
            data["debug_url"] = debug_url
        return InternalError(data)


class ServerError(Error):
    """Something else went wrong."""
    code = -32000
    message = "Server error"


class InvalidReturnTypeError(Error):
    """Return type does not match expected type."""
    code = -32001
    message = "Invalid return type"
