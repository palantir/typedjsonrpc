"""Data structure for wrapping methods and information about them."""

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
            "params": self.parameters,
            "returns": self.return_type,
            "description": self.description,
        }

    @property
    def parameters(self):
        if self.signature is not None:
            return [{"name": p_name, "type": p_type.__name__}
                    for (p_name, p_type) in self.signature["parameter_types"]]
        return None

    @property
    def return_type(self):
        if self.signature is not None:
            returns = self.signature["returns"]
            none_type = type(None)
            if returns is not None and returns is not none_type:
                return returns.__name__

    @property
    def description(self):
        return self.method.__doc__
