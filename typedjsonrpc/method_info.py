"""This module contains a data structure for wrapping methods and information about them."""

__all__ = ["MethodInfo"]


class MethodInfo(object):
    """An object wrapping a method and information about it."""

    def __init__(self, name, method, signature=None):
        self._name = name
        self._method = method
        self._signature = signature

    def describe(self):
        """Describes the method.
        :return: Description
        :rtype: dict[str, object]
        """
        return {
            "name": self._name,
            "params": self._get_parameters(),
            "docstring": self._method.__doc__
        }

    def get_method(self):
        """Returns the method.
        :return: The method
        :rtype: function
        """
        return self._method

    def _get_parameters(self):
        if self._signature is not None:
            return [{"name": p_name, "type": p_type}
                    for (p_name, p_type) in self._signature]
        return None
