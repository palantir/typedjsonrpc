"""This module contains logic for storing and calling jsonrpc methods."""
import inspect
import json
import six
import wrapt

from typedjsonrpc.errors import (Error, InternalError, InvalidParamsError, InvalidReturnTypeError,
                                 InvalidRequestError, MethodNotFoundError, ParseError)
from typedjsonrpc.method_info import MethodInfo
from werkzeug.debug.tbtools import get_current_traceback

__all__ = ["Registry"]

RETURNS_KEY = "returns"


class Registry(object):
    """The registry for storing and calling jsonrpc methods.

    :attribute debug: Debug option which enables recording of tracebacks
    :type debug: bool
    :attribute tracebacks: Tracebacks for debugging
    :type tracebacks: dict[int, werkzeug.debug.tbtools.Traceback]
    """

    def __init__(self, debug=False):
        """
        :param debug: If True, the registry records tracebacks for debugging purposes
        :type debug: bool
        """
        self._name_to_method_info = {}
        self._register_describe()
        self.debug = debug
        self.tracebacks = {}

    def _register_describe(self):
        def _describe():
            return self.describe()
        _describe.__doc__ = self.describe.__doc__

        describe_signature = self._get_signature([], {"returns": dict})
        self.register("rpc.describe", _describe, describe_signature)

    def dispatch(self, request):
        """Takes a request and dispatches its data to a jsonrpc method.

        :param request: a werkzeug request with json data
        :type request: werkzeug.wrappers.Request
        :returns: json output of the corresponding method
        :rtype: str
        """
        def _wrapped():
            messages = self._get_request_messages(request)
            result = [self._dispatch_and_handle_errors(message) for message in messages]
            non_notification_result = [x for x in result if x is not None]
            if len(non_notification_result) == 0:
                return
            elif len(messages) == 1:
                return non_notification_result[0]
            else:
                return non_notification_result

        result = self._handle_exceptions(_wrapped)
        if result is not None:
            return json.dumps(result)

    def _dispatch_and_handle_errors(self, msg):
        is_notification = isinstance(msg, dict) and "id" not in msg

        def _wrapped():
            result = self._dispatch_message(msg)
            if not is_notification:
                return Registry._create_result_response(msg["id"], result)

        return self._handle_exceptions(_wrapped, is_notification, self._get_id_if_known(msg))

    def _handle_exceptions(self, method, is_notification=False, msg_id=None):
        try:
            return method()
        except Error as exc:
            if not is_notification:
                if self.debug:
                    debug_url = self._store_traceback()
                    exc.data = {"message": exc.data, "debug_url": debug_url}
                return Registry._create_error_response(msg_id, exc)
        except Exception as exc:  # pylint: disable=broad-except
            if not is_notification:
                if self.debug:
                    debug_url = self._store_traceback()
                else:
                    debug_url = None
                new_error = InternalError.from_error(exc, debug_url)
                return Registry._create_error_response(msg_id, new_error)

    def _store_traceback(self):
        traceback = get_current_traceback(skip=1,
                                          show_hidden_frames=False,
                                          ignore_system_exceptions=True)
        self.tracebacks[traceback.id] = traceback
        return "/debug/{}".format(traceback.id)

    @staticmethod
    def _get_id_if_known(msg):
        if isinstance(msg, dict) and "id" in msg:
            return msg["id"]
        else:
            return None

    def _dispatch_message(self, msg):
        self._check_request(msg)
        method = self._name_to_method_info[msg["method"]].method
        params = msg.get("params", [])
        Registry._validate_params_match(method, params)
        if isinstance(params, list):
            result = method(*params)
        elif isinstance(params, dict):
            result = method(**params)
        else:
            raise InvalidRequestError("Given params '%s' are neither a list nor a dict."
                                      % (msg["params"],))
        return result

    @staticmethod
    def _create_result_response(msg_id, result):
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result,
        }

    @staticmethod
    def _create_error_response(msg_id, exc):
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": exc.as_error_object(),
        }

    def register(self, name, method, parameter_types=None):
        """Registers a method with a given name and signature.

        :param name: The name used to register the method
        :type name: str
        :param method: The method to register
        :type method: function
        :param parameter_types: List of the parameter names and types
        :type parameter_types: list[str, type]
        """
        if inspect.ismethod(method):
            raise Exception("typedjsonrpc does not support making class methods into endpoints")
        self._name_to_method_info[name] = MethodInfo(name, method, parameter_types)

    def method(self, **parameter_types):
        """Syntactic sugar for registering a method

        Example:

            >>> registry = Registry()
            >>> @registry.method(returns=int, x=int, y=int)
            ... def add(x, y):
            ...     return x + y

        :param parameter_types: The types of the method's parameters
        :type parameter_types: dict[str,type]
        """
        @wrapt.decorator
        def type_check_wrapper(method, instance, args, kwargs):
            """Wraps a method so that it is type-checked.

            :param method: The method to wrap
            :type method: (T) -> U
            :return: The result of calling the method with the given parameters
            :rtype: U
            """
            if instance is not None:
                raise Exception("Instance shouldn't be set.")

            parameter_names = inspect.getargspec(method).args
            defaults = inspect.getargspec(method).defaults
            parameters = self._collect_parameters(parameter_names, args, kwargs, defaults)

            param_types = parameter_types.copy()
            return_type = param_types.pop(RETURNS_KEY)
            self._check_types(parameters, param_types)

            result = method(*args, **kwargs)
            self._check_return_type(result, return_type)

            return result

        def register_method(method):
            """Registers a method with its fully qualified name.

            :param method: The method to register
            :type method: (T) -> U
            :return: The original method wrapped into a type-checker
            :rtype: (T) -> U
            """
            parameter_names = inspect.getargspec(method).args
            self._check_type_declaration(parameter_names, parameter_types)

            wrapped_method = type_check_wrapper(method, None, None, None)
            fully_qualified_name = "{}.{}".format(method.__module__, method.__name__)
            self.register(fully_qualified_name, wrapped_method,
                          self._get_signature(parameter_names, parameter_types))
            return wrapped_method

        return register_method

    @staticmethod
    def _collect_parameters(parameter_names, args, kwargs, defaults):
        """Creates a dictionary mapping parameters names to their values in the method call.

        :param parameter_names: The method's parameter names
        :type parameter_names: list[string]
        :param args: *args passed into the method
        :type args: list[object]
        :param kwargs: **kwargs passed into the method
        :type kwargs: dict[string, object]
        :param defaults: The method's default values
        :type defaults: list[object]
        :return: Dictionary mapping parameter names to values
        :rtype: dict[string, object]
        """
        parameters = {}
        if defaults is not None:
            zipped_defaults = zip(reversed(parameter_names), reversed(defaults))
            for name, default in zipped_defaults:
                parameters[name] = default
        for name, value in zip(parameter_names, args):
            parameters[name] = value
        for name, value in kwargs.items():
            parameters[name] = value
        return parameters

    def describe(self):
        """Returns a description of all the methods in the registry.

        :return: Description
        :rtype: dict[str, object]
        """
        return {
            "methods": [method_info.describe()
                        for method_info in sorted(self._name_to_method_info.values())]
        }

    @staticmethod
    def _get_request_messages(request):
        """Parses the request as a json message.

        :param request: a werkzeug request with json data
        :type request: werkzeug.wrappers.Request
        :return: The parsed json object
        :rtype: dict[str, object]
        """
        data = request.get_data()
        try:
            msg = json.loads(data)
        except Exception:
            raise ParseError("Could not parse request data '%s'" % (data,))
        if isinstance(msg, list):
            return msg
        else:
            return [msg]

    def _check_request(self, msg):
        """Checks that the request json is well-formed.

        :param msg: The request's json data
        :type msg: dict[str, object]
        """
        if "jsonrpc" not in msg:
            raise InvalidRequestError("'\"jsonrpc\": \"2.0\"' must be included.")
        if msg["jsonrpc"] != "2.0":
            raise InvalidRequestError("'jsonrpc' must be exactly the string '2.0', but it was '%s'."
                                      % (msg["jsonrpc"],))
        if "method" not in msg:
            raise InvalidRequestError("No method specified.")
        if "id" in msg:
            if msg["id"] is None:
                raise InvalidRequestError("typedjsonrpc does not allow id to be None.")
            if isinstance(msg["id"], float):
                raise InvalidRequestError("typedjsonrpc does not support float ids.")
            if not isinstance(msg["id"], (six.string_types, int)):
                raise InvalidRequestError("id must be a string or integer; '%s' is of type %s."
                                          % (msg["id"], type(msg["id"])))
        if msg["method"] not in self._name_to_method_info:
            raise MethodNotFoundError("Could not find method '%s'." % (msg["method"],))

    @staticmethod
    def _validate_params_match(method, parameters):
        argspec = inspect.getargspec(method)
        default_length = len(argspec.defaults) if argspec.defaults is not None else 0
        if isinstance(parameters, list):
            if len(parameters) > len(argspec.args) and argspec.varargs is None:
                raise InvalidParamsError("Too many parameters")

            remaining_parameters = len(argspec.args) - len(parameters)
            if remaining_parameters > default_length:
                raise InvalidParamsError("Not enough parameters")
        elif isinstance(parameters, dict):
            missing_parameters = [key for key in argspec.args if key not in parameters]
            default_parameters = set(argspec.args[len(argspec.args) - default_length:])
            for key in missing_parameters:
                if key not in default_parameters:
                    raise InvalidParamsError("Parameter %s has not been satisfied" % (key,))

            extra_params = [key for key in parameters if key not in argspec.args]
            if len(extra_params) > 0 and argspec.keywords is None:
                raise InvalidParamsError("Too many parameters")

    @staticmethod
    def _check_types(parameters, parameter_types):
        """Checks that the given parameters have the correct types.

        :param parameters: List of (name, value) pairs of the given parameters
        :type parameters: list[(str, object)]
        :param parameter_types: Parameter type by name.
        :type parameter_types: dict[str,type]
        """
        for name, parameter_type in parameter_types.items():
            if name not in parameters:
                raise InvalidParamsError("Parameter '%s' is missing." % (name,))
            if not isinstance(parameters[name], parameter_type):
                raise InvalidParamsError("Value '%s' for parameter '%s' is not of expected type %s."
                                         % (parameters[name], name, parameter_type))

    @staticmethod
    def _check_type_declaration(parameter_names, parameter_types):
        """Checks that exactly the given parameter names have declared types.

        :param parameter_names: The names of the parameters in the method declaration
        :type parameter_names: list[str]
        :param parameter_types: Parameter type by name
        :type parameter_types: dict[str, type]
        """
        if RETURNS_KEY in parameter_names:
            raise Exception("'%s' may not be used as a parameter name" % (RETURNS_KEY,))
        if RETURNS_KEY not in parameter_types:
            raise Exception("Missing return type declaration")
        if len(parameter_names) != len(parameter_types) - 1:
            raise Exception("Number of method parameters (%s) does not match number of "
                            "declared types (%s)"
                            % (len(parameter_names), len(parameter_types) - 1))
        for parameter_name in parameter_names:
            if parameter_name not in parameter_types:
                raise Exception("Parameter '%s' does not have a declared type" % (parameter_name,))

    @staticmethod
    def _check_return_type(value, expected_type):
        """Checks that the given return value has the correct type.

        :param value: Value returned by the method
        :type value: any
        :param expected_type: Expected return type
        :type expected_type: type
        """
        if expected_type is None:
            if value is not None:
                raise InvalidReturnTypeError("Returned value is '%s' but None was expected"
                                             % (value,))
        elif not isinstance(value, expected_type):
            raise InvalidReturnTypeError("Type of return value '%s' does not match expected type %s"
                                         % (value, expected_type))

    @staticmethod
    def _get_signature(parameter_names, parameter_types):
        return {
            "returns": parameter_types[RETURNS_KEY],
            "parameter_types": [(name, parameter_types[name]) for name in parameter_names]
        }
