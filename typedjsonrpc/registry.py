"""This module contains logic for storing and calling jsonrpc methods."""
import inspect
import json
import wrapt

__all__ = ["Registry"]

RETURNS_KEY = "returns"


class Registry(object):
    """The registry for storing and calling jsonrpc methods."""

    def __init__(self):
        self._name_to_method = {}

    def dispatch(self, request):
        """Takes a request and dispatches its data to a jsonrpc method.

        :param request: a werkzeug request with json data
        :type request: werkzeug.wrappers.Request

        :returns: json output of the corresponding function
        :rtype: str
        """
        msg = json.loads(request.get_data())
        func = self._name_to_method[msg["method"]]
        if isinstance(msg["params"], list):
            return json.dumps(func(*msg["params"]))
        elif isinstance(msg["params"], dict):
            return json.dumps(func(**msg["params"]))
        else:
            raise Exception("Invalid params type")

    def register(self, name, method):
        """Registers a method with a given name.
        :param name: The name to register
        :type name: str
        :param method: The function to call
        :type method: function
        """
        self._name_to_method[name] = method

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

            self._check_types(zip(argument_names, args), argtypes)
            self._check_types(kwargs.items(), argtypes)

            result = func(*args, **kwargs)
            self._check_return_type(result, argtypes[RETURNS_KEY])

            return result

        def register_function(func):
            """ Registers a method with its fully qualified name.
            :param func: The function to register
            :type func: (T) -> U
            :return: The original function wrapped into a type-checker
            :rtype: (T) -> U
            """
            self._check_type_declaration(inspect.getargspec(func).args, argtypes)

            wrapped_function = type_check_wrapper(func, None, None, None)
            fully_qualified_name = "{}.{}".format(func.__module__, func.__name__)
            self._name_to_method[fully_qualified_name] = wrapped_function

            return wrapped_function

        return register_function

    @staticmethod
    def _check_types(arguments, argument_types):
        """ Checks that the given arguments have the correct types.
        :param arguments: List of (name, value) pairs of the given arguments
        :type arguments: list[(str, object)]
        :param argument_types: Argument type by name.
        :type argument_types: dict[str,type]
        """
        for name, value in arguments:
            if name not in argument_types:
                raise TypeError("Argument '%s' is not expected" % (name,))
            if not isinstance(value, argument_types[name]):
                raise TypeError("Value '%s' for argument '%s' is not of expected type %s"
                                % (value, name, argument_types[name]))

    @staticmethod
    def _check_type_declaration(argument_names, type_declarations):
        """ Checks that exactly the given argument names have declared types.
        :param argument_names: The names of the arguments in the function declaration
        :type argument_names: list[str]
        :param type_declarations: Argument type by name
        :type type_declarations: dict[str, type]
        """
        if len(argument_names) != len(type_declarations) - 1:
            raise Exception("Number of function arguments (%s) does not match number of "
                            "declared types (%s)"
                            % (len(argument_names), len(type_declarations) - 1))
        if RETURNS_KEY in argument_names:
            raise Exception("'%s' may not be used as an argument name" % (RETURNS_KEY,))
        if RETURNS_KEY not in type_declarations:
            raise Exception("Missing return type declaration")
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
