"""This module contains logic for storing and calling jsonrpc methods."""
import json


__all__ = ["Registry"]


class Registry(object):
    """The registry for storing and calling jsonrpc methods."""

    def __init__(self):
        self._name_to_method = {}

    def dispatch(self, request):
        """Takes a request and dispatches its data to a jsonrpc method.
        :param werkzeug.wrappers.Request request:
        :return: json string of the function returned
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
        :param str name: The name to register
        :param function method:  The function to call
        """
        self._name_to_method[name] = method

    def method(self):
        """Syntactic sugar for registering a method"""
        def wrapper(func):
            """Registers a method with its fully qualified name.

            :param function func: The function to register
            :return: The original function unmodified
            """
            fully_qualified_name = "{}.{}".format(func.__module__, func.__name__)
            self._name_to_method[fully_qualified_name] = func
            return func

        return wrapper
