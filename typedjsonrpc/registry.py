"""This module contains logic for storing and calling jsonrpc methods."""
import inspect
import json
import wrapt

from typedjsonrpc.method_info import MethodInfo

__all__ = ["Registry"]

RETURNS_KEY = "returns"


class Registry(object):
    """The registry for storing and calling jsonrpc methods."""

    def __init__(self):
        self._name_to_method_info = {}

    def dispatch(self, request):
        """Takes a request and dispatches its data to a jsonrpc method.

        :param request: a werkzeug request with json data
        :type request: werkzeug.wrappers.Request

        :returns: json output of the corresponding function
        :rtype: str
        """
        msg = json.loads(request.get_data())
        func = self._name_to_method_info[msg["method"]].get_method()
        if isinstance(msg["params"], list):
            result = func(*msg["params"])
        elif isinstance(msg["params"], dict):
            result = func(**msg["params"])
        else:
            raise Exception("Invalid params type")
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
            "functions": [method_info.describe()
                          for method_info in self._name_to_method_info.values()]
        }

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
                raise TypeError("Argument '%s' is missing" % (name,))
            if not isinstance(arguments[name], arg_type):
                raise TypeError("Value '%s' for argument '%s' is not of expected type %s"
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
                raise TypeError("Returned value is '%s' but None was expected" % (value,))
        elif not isinstance(value, expected_type):
            raise TypeError("Type of return value '%s' does not match expected type %s"
                            % (value, expected_type))

    @staticmethod
    def _get_signature(arg_names, arg_types):
        argument_types = []
        for name in arg_names:
            argument_types.append((name, arg_types[name]))
        return {
            "returns": arg_types[RETURNS_KEY],
            "argument_types": argument_types
        }
