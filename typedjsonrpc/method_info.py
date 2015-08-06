"""Data structure for wrapping methods and information about them."""

from collections import namedtuple

__all__ = ["MethodInfo"]


class MethodInfo(namedtuple("MethodInfo", ["name", "method", "signature"])):
    """An object wrapping a method and information about it.

    :attribute name: Name of the function
    :type name: str
    :attribute method: The function being described
    :type method: function
    :attribute signature: A description of the types this method takes as parameters and returns
    :type signature: list[str, type]
    """

    def describe(self):
        """Describes the method.

        :return: Description
        :rtype: dict[str, object]
        """
        return {
            "name": self.name,
            "params": self.parameters,
            "returns": self.return_type,
            "description": self.description,
        }

    @property
    def parameters(self):
        """The parameters for this method in a JSON-compatible format

        :rtype: list[dict[str, str]] or None
        """
        if self.signature is not None:
            return [{"name": p_name, "type": p_type.__name__}
                    for (p_name, p_type) in self.signature["parameter_types"]]
        return None

    @property
    def return_type(self):
        """The return type for this method in a JSON-compatible format.

        This handles the special case of ``None`` which allows ``type(None)`` also.
        :rtype: str or None
        """
        if self.signature is not None:
            returns = self.signature["returns"]
            none_type = type(None)
            if returns is not None and returns is not none_type:
                return returns.__name__

    @property
    def description(self):
        """Returns the docstring for this method.

        :rtype: str
        """
        return self.method.__doc__
