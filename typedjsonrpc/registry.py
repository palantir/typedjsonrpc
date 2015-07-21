"""This module contains logic for storing and calling jsonrpc methods."""
import inspect
import json
import wrapt

__all__ = ["Registry"]


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
        :param argtypes: The types of the function's parameters
        :type argtypes: dict[str,type]
        """
        @wrapt.decorator
        def type_check_wrapper(func, instance, args, kwargs):
            """ Wraps a function so that it is type-checked.
            :param func: The function to wrap
            :type func: function
            :return: The original function wrapped into a type-checker
            :rtype: function
            """
            if instance is not None:
                raise Exception("Instance shouldn't be set.")

            argument_names = inspect.getargspec(func).args

            self._check_types(zip(argument_names, args), argtypes)
            self._check_types(kwargs.items(), argtypes)

            return func(*args, **kwargs)

        def register_function(func):
            """ Registers a method with its fully qualified name.
            :param func: The function to register
            :type func: function
            :return: The original function wrapped into a type-checker
            :rtype: function
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
        :type arguments: list
        :param argument_types: Parameter type by name.
        :type argument_types: dict[str,type]
        """
        for name, value in arguments:
            if name not in argument_types:
                raise TypeError("Argument '%s' is not expected" % (name,))
            if not isinstance(value, argument_types[name]):
                raise TypeError("Value '%s' for parameter '%s' is not of expected type %s"
                                % (value, name, argument_types[name]))

    @staticmethod
    def _check_type_declaration(parameter_names, type_declarations):
        """ Checks that exactly the given parameter names have declared types.
        :param parameter_names: The names of the parameters in the function declaration
        :type parameter_names: list
        :param type_declarations: Parameter type by name
        :type type_declarations: dict[str, type]
        """
        if len(parameter_names) != len(type_declarations):
            raise Exception("Number of function arguments (%s) does not match number of "
                            "declared types (%s)"
                            % (len(parameter_names), len(type_declarations)))
        for arg in parameter_names:
            if arg not in type_declarations:
                raise Exception("Argument '%s' does not have a declared type" % (arg,))
