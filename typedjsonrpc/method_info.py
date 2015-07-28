"""This module contains a data structure for wrapping methods and information about them."""

from collections import namedtuple

__all__ = ["MethodInfo"]


class MethodInfo(namedtuple("MethodInfo", ["name", "method", "signature"])):
    """An object wrapping a method and information about it."""

    def describe(self):
        """Describes the method.
        :return: Description
        :rtype: dict[str, object]
        """
        return {
            "name": self.name,
            "params": self._get_parameters(),
            "returns": self._get_return_type(),
            "description": self.method.__doc__
        }

    def get_method(self):
        """Returns the method.
        :return: The method
        :rtype: function
        """
        return self.method

    def _get_parameters(self):
        if self.signature is not None:
            return [{"name": p_name, "type": p_type.__name__}
                    for (p_name, p_type) in self.signature["argument_types"]]
        return None

    def _get_return_type(self):
        if self.signature is not None:
            return_type = self.signature["returns"]
            none_type = type(None)
            if return_type is not None and return_type is not none_type:
                return return_type.__name__
