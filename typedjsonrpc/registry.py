"""This module contains logic for storing and calling jsonrpc methods."""
import inspect
import json
import six
import wrapt

from typedjsonrpc.errors import (InvalidParamsError, InvalidReturnTypeError, InvalidRequestError,
                                 MethodNotFoundError, ParseError)
from typedjsonrpc.method_info import MethodInfo

__all__ = ["Registry"]

RETURNS_KEY = "returns"


class Registry(object):
    """The registry for storing and calling jsonrpc methods."""

    def __init__(self):
        self._name_to_method_info = {}
        self._register_describe()

    def _register_describe(self):
        def _describe():
            self.describe()
        _describe.__doc__ = self.describe.__doc__

        describe_signature = self._get_signature([], {"returns": dict})
        self.register("rpc.describe", _describe, describe_signature)

    def dispatch(self, request):
        """Takes a request and dispatches its data to a jsonrpc method.

        :param request: a werkzeug request with json data
        :type request: werkzeug.wrappers.Request

        :returns: json output of the corresponding function
        :rtype: str
        """
        msg = self._get_request_message(request)
        self._check_request(msg)
        func = self._name_to_method_info[msg["method"]].method
        params = msg.get("params", [])
        Registry._validate_params_match(func, params)
        if isinstance(params, list):
            result = func(*params)
        elif isinstance(params, dict):
            result = func(**params)
        else:
            raise InvalidRequestError("Given params '%s' are neither a list nor a dict."
                                      % (msg["params"],))
        if "id" in msg:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg["id"],
                "result": result
            })

    def register(self, name, method, signature=None):
        """Registers a method with a given name and signature.

        :param name: The name to register
        :type name: str
        :param method: The function to call
        :type method: function
        :param signature: List of the argument names and types
        :type signature: list[str, type]
        """
        if inspect.ismethod(method):
            raise Exception("typedjsonrpc does not support making class methods into endpoints")
        self._name_to_method_info[name] = MethodInfo(name, method, signature)

    def method(self, **argtypes):
        """ Syntactic sugar for registering a method

        Example:

            >>> registry = Registry()
            >>> @registry.method(returns=int, x=int, y=int)
            ... def add(x, y):
            ...     return x + y

        :param argtypes: The types of the function's arguments
        :type argtypes: dict[str,type]
        """
        @wrapt.decorator
        def type_check_wrapper(func, instance, args, kwargs):
            """ Wraps a function so that it is type-checked.

            :param func: The function to wrap
            :type func: (T) -> U

            :return: The original function wrapped into a type-checker
            :rtype: (T) -> U
            """
            if instance is not None:
                raise Exception("Instance shouldn't be set.")

            argument_names = inspect.getargspec(func).args
            defaults = inspect.getargspec(func).defaults
            arguments = self._collect_arguments(argument_names, args, kwargs, defaults)

            argument_types = argtypes.copy()
            return_type = argument_types.pop(RETURNS_KEY)
            self._check_types(arguments, argument_types)

            result = func(*args, **kwargs)
            self._check_return_type(result, return_type)

            return result

        def register_function(func):
            """ Registers a method with its fully qualified name.

            :param func: The function to register
            :type func: (T) -> U

            :return: The original function wrapped into a type-checker
            :rtype: (T) -> U
            """
            arg_names = inspect.getargspec(func).args
            self._check_type_declaration(arg_names, argtypes)

            wrapped_function = type_check_wrapper(func, None, None, None)
            fully_qualified_name = "{}.{}".format(func.__module__, func.__name__)
            self.register(fully_qualified_name, wrapped_function,
                          self._get_signature(arg_names, argtypes))
            return wrapped_function

        return register_function

    @staticmethod
    def _collect_arguments(argument_names, args, kwargs, defaults):
        """ Creates a dictionary mapping argument names to their values in the function call.
        :param argument_names: The function's argument names
        :type argument_names: list[string]
        :param args: *args passed into the function
        :type args: list[object]
        :param kwargs: **kwargs passed into the function
        :type kwargs: dict[string, object]
        :param defaults: The function's default values
        :type defaults: list[object]
        :return: Dictionary mapping argument names to values
        :rtype: dict[string, object]
        """
        arguments = {}
        if defaults is not None:
            zipped_defaults = zip(reversed(argument_names), reversed(defaults))
            for name, default in zipped_defaults:
                arguments[name] = default
        for name, value in zip(argument_names, args):
            arguments[name] = value
        for name, value in kwargs.items():
            arguments[name] = value
        return arguments

    def describe(self):
        """ Returns a description of all the functions in the registry.
        :return: Description
        """
        return {
            "methods": [method_info.describe()
                        for method_info in sorted(self._name_to_method_info.values())]
        }

    @staticmethod
    def _get_request_message(request):
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
        return msg

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
    def _validate_params_match(func, params):
        argspec = inspect.getargspec(func)
        default_length = len(argspec.defaults) if argspec.defaults is not None else 0
        if isinstance(params, list):
            if len(params) > len(argspec.args) and argspec.varargs is None:
                raise InvalidParamsError("Too many arguments")

            remaining_args = len(argspec.args) - len(params)
            if remaining_args > default_length:
                raise InvalidParamsError("Not enough arguments")
        elif isinstance(params, dict):
            missing_args = [key for key in argspec.args if key not in params]
            default_args = set(argspec.args[len(argspec.args) - default_length:])
            for key in missing_args:
                if key not in default_args:
                    raise InvalidParamsError("Argument %s has not been satisfied" % (key,))

            extra_params = [key for key in params if key not in argspec.args]
            if len(extra_params) > 0 and argspec.keywords is None:
                raise InvalidParamsError("Too many arguments")

    @staticmethod
    def _check_types(arguments, argument_types):
        """ Checks that the given arguments have the correct types.

        :param arguments: List of (name, value) pairs of the given arguments
        :type arguments: list[(str, object)]

        :param argument_types: Argument type by name.
        :type argument_types: dict[str,type]
        """
        for name, arg_type in argument_types.items():
            if name not in arguments:
                raise InvalidParamsError("Argument '%s' is missing." % (name,))
            if not isinstance(arguments[name], arg_type):
                raise InvalidParamsError("Value '%s' for argument '%s' is not of expected type %s."
                                         % (arguments[name], name, arg_type))

    @staticmethod
    def _check_type_declaration(argument_names, type_declarations):
        """ Checks that exactly the given argument names have declared types.

        :param argument_names: The names of the arguments in the function declaration
        :type argument_names: list[str]

        :param type_declarations: Argument type by name
        :type type_declarations: dict[str, type]
        """
        if RETURNS_KEY in argument_names:
            raise Exception("'%s' may not be used as an argument name" % (RETURNS_KEY,))
        if RETURNS_KEY not in type_declarations:
            raise Exception("Missing return type declaration")
        if len(argument_names) != len(type_declarations) - 1:
            raise Exception("Number of function arguments (%s) does not match number of "
                            "declared types (%s)"
                            % (len(argument_names), len(type_declarations) - 1))
        for arg in argument_names:
            if arg not in type_declarations:
                raise Exception("Argument '%s' does not have a declared type" % (arg,))

    @staticmethod
    def _check_return_type(value, expected_type):
        """ Checks that the given return value has the correct type.
        :param value: Value returned by the function
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
    def _get_signature(arg_names, arg_types):
        return {
            "returns": arg_types[RETURNS_KEY],
            "argument_types": [(name, arg_types[name]) for name in arg_names]
        }
