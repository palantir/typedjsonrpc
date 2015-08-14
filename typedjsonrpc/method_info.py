#
# Copyright 2015 Palantir Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Data structures for wrapping methods and information about them."""

from collections import namedtuple

__all__ = ["MethodInfo"]


class MethodInfo(namedtuple("MethodInfo", ["name", "method", "signature"])):
    """An object wrapping a method and information about it.

    :attribute name: Name of the function
    :type name: str
    :attribute method: The function being described
    :type method: function
    :attribute signature: A description of the types this method takes as parameters and returns
    :type signature: MethodSignature
    """

    def describe(self):
        """Describes the method.

        :return: Description
        :rtype: dict[str, object]
        """
        return {
            "name": self.name,
            "params": self.params,
            "returns": self.returns,
            "description": self.description,
        }

    @property
    def params(self):
        """The parameters for this method in a JSON-compatible format

        :rtype: list[dict[str, str]]
        """
        return [{"name": p_name, "type": p_type.__name__}
                for (p_name, p_type) in self.signature.parameter_types]

    @property
    def returns(self):
        """The return type for this method in a JSON-compatible format.

        This handles the special case of ``None`` which allows ``type(None)`` also.

        :rtype: str or None
        """
        return_type = self.signature.return_type
        none_type = type(None)
        if return_type is not None and return_type is not none_type:
            return return_type.__name__

    @property
    def description(self):
        """Returns the docstring for this method.

        :rtype: str
        """
        return self.method.__doc__


class MethodSignature(namedtuple("MethodSignature", ["parameter_types", "return_type"])):
    """Represents the types which a function takes as input and output.

    :attribute parameter_types: A list of tuples mapping strings to type with a specified order
    :type parameter_types: list[str, type]
    :attribute return_type: The type which the function returns
    :type return_type: type
    """

    @staticmethod
    def create(parameter_names, parameter_types, return_type):
        """Returns a signature object ensuring order of parameter names and types.

        :param parameter_names: A list of ordered parameter names
        :type parameter_names: list[str]
        :param parameter_types: A dictionary of parameter names to types
        :type parameter_types: dict[str, type]
        :param return_type: The type the function returns
        :type return_type: type
        :rtype: MethodSignature
        """
        ordered_pairs = [(name, parameter_types[name]) for name in parameter_names]
        return MethodSignature(ordered_pairs, return_type)
