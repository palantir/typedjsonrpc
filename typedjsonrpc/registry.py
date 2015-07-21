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
        """Syntactic sugar for registering a method"""
        @wrapt.decorator
        def type_check_wrapper(wrapped, instance, args, kwargs):
            """ Wraps a function so that it is type-checked.
            :param function func: The function to wrap
            :return: The original function wrapped into a type-checker
            """
            if instance is not None:
                raise Exception("Instance shouldn't be set.")

            argument_names = inspect.getargspec(wrapped).args

            self.check_types(zip(argument_names, args), argtypes)
            self.check_types(kwargs.items(), argtypes)

            return wrapped(*args, **kwargs)

        def register_function(func):
            """ Registers a method with its fully qualified name.
            :param function func: The function to register
            :return: The original function wrapped into a type-checker
            """
            self.check_type_declaration(inspect.getargspec(func).args, argtypes)

            wrapped_function = type_check_wrapper(func, None, None, None)
            fully_qualified_name = "{}.{}".format(func.__module__, func.__name__)
            self._name_to_method[fully_qualified_name] = wrapped_function
            return wrapped_function

        return register_function

    @staticmethod
    def check_types(arguments, argument_types):
        """ Checks that the given arguments have the correct types.
        :param list arguments: (name, value) of the given arguments
        :param dict argument_types: Parameter type by name.
        """
        for name, value in arguments:
            if name not in argument_types:
                raise TypeError("Argument '%s' is not expected" % (name,))
            if not isinstance(value, argument_types[name]):
                raise TypeError("Value '%s' for parameter '%s' is not of expected type %s"
                                % (value, name, argument_types[name]))

    @staticmethod
    def check_type_declaration(parameter_names, type_declarations):
        """ Checks that exactly the given parameter names have declared types.
        :param list parameter_names: The names of the parameters in the function declaration
        :param dict type_declarations: Parameter type by name
        """
        if len(parameter_names) != len(type_declarations):
            raise Exception("Number of function arguments (%s) does not match number of "
                            "declared types (%s)"
                            % (len(parameter_names), len(type_declarations)))
        for arg in parameter_names:
            if arg not in type_declarations:
                raise Exception("Argument '%s' does not have a declared type" % (arg,))
