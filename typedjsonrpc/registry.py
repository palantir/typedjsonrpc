"""This module contains logic for storing and calling jsonrpc methods."""
import json
import inspect
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
            # More arguments in call than in declaration?
            if len(args) > len(argument_names):
                raise TypeError("Number of arguments (%s) is less than number"
                                "of declared arguments (%s)." % (len(args), len(argument_names)))
            # Check types of args
            for i in range(0, len(args)):
                if not isinstance(args[i], argtypes[argument_names[i]]):
                    raise TypeError("Value '%s' is not of expected type %s"
                                    % (args[i], argtypes[argument_names[i]]))
            # Check types of kwargs
            for key, value in kwargs.items():
                if key not in argtypes.keys():
                    raise TypeError("Argument '%s' is not expected" % key)
                if not isinstance(value, argtypes[key]):
                    raise TypeError("Value '%s' for argument '%s' is not of type %s"
                                    % (value, key, argtypes[key]))
            # Call the original method
            return wrapped(*args, **kwargs)

        def register_function(func):
            """ Registers a method with its fully qualified name.
            :param function func: The function to register
            :return: The original function wrapped into a type-checker
            """
            # Check that exactly the parameter names of the function have declared types
            function_arguments = inspect.getargspec(func).args
            type_declarations = argtypes.items()
            if len(function_arguments) != len(type_declarations):
                raise TypeError("Number of function arguments (%s) does not match number of "
                                "declared types (%s)"
                                % (len(function_arguments), len(type_declarations)))
            for arg in function_arguments:
                if arg not in argtypes.keys():
                    raise TypeError("Argument '%s' does not have a declared type" % arg)

            wrapped_function = type_check_wrapper(func, None, None, None)
            fully_qualified_name = "{}.{}".format(func.__module__, func.__name__)
            self._name_to_method[fully_qualified_name] = wrapped_function
            return wrapped_function

        return register_function
