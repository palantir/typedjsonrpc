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

"""Logic for checking parameter declarations and parameter types."""
import inspect
import six

from typedjsonrpc.errors import InvalidParamsError, InvalidReturnTypeError


def validate_params_match(method, parameters):
    """Validates that the given parameters are exactly the method's declared parameters.

    :param method: The method to be called
    :type method: function
    :param parameters: The parameters to use in the call
    :type parameters: dict[str, object] | list[object]
    """
    argspec = inspect.getargspec(method)
    default_length = len(argspec.defaults) if argspec.defaults is not None else 0

    if isinstance(parameters, list):
        if len(parameters) > len(argspec.args) and argspec.varargs is None:
            raise InvalidParamsError("Too many parameters")

        remaining_parameters = len(argspec.args) - len(parameters)
        if remaining_parameters > default_length:
            raise InvalidParamsError("Not enough parameters")

    elif isinstance(parameters, dict):
        missing_parameters = [key for key in argspec.args if key not in parameters]
        default_parameters = set(argspec.args[len(argspec.args) - default_length:])
        for key in missing_parameters:
            if key not in default_parameters:
                raise InvalidParamsError("Parameter {} has not been satisfied".format(key))

        extra_params = [key for key in parameters if key not in argspec.args]
        if len(extra_params) > 0 and argspec.keywords is None:
            raise InvalidParamsError("Too many parameters")


def check_types(parameters, parameter_types):
    """Checks that the given parameters have the correct types.

    :param parameters: List of (name, value) pairs of the given parameters
    :type parameters: dict[str, object]
    :param parameter_types: Parameter type by name.
    :type parameter_types: dict[str, type]
    """
    for name, parameter_type in parameter_types.items():
        if name not in parameters:
            raise InvalidParamsError("Parameter '{}' is missing.".format(name))
        if not _is_instance(parameters[name], parameter_type):
            raise InvalidParamsError("Value '{}' for parameter '{}' is not of expected type {}."
                                     .format(parameters[name], name, parameter_type))


def check_type_declaration(parameter_names, parameter_types):
    """Checks that exactly the given parameter names have declared types.

    :param parameter_names: The names of the parameters in the method declaration
    :type parameter_names: list[str]
    :param parameter_types: Parameter type by name
    :type parameter_types: dict[str, type]
    """
    if len(parameter_names) != len(parameter_types):
        raise Exception("Number of method parameters ({}) does not match number of "
                        "declared types ({})"
                        .format(len(parameter_names), len(parameter_types)))
    for parameter_name in parameter_names:
        if parameter_name not in parameter_types:
            raise Exception("Parameter '{}' does not have a declared type".format(parameter_name))


def check_return_type(value, expected_type):
    """Checks that the given return value has the correct type.

    :param value: Value returned by the method
    :type value: object
    :param expected_type: Expected return type
    :type expected_type: type
    """
    if expected_type is None:
        if value is not None:
            raise InvalidReturnTypeError("Returned value is '{}' but None was expected"
                                         .format(value))
    elif not _is_instance(value, expected_type):
        raise InvalidReturnTypeError("Type of return value '{}' does not match expected type {}"
                                     .format(value, expected_type))


def _is_instance(value, expected_type):
    if expected_type is int:
        return isinstance(value, six.integer_types)
    else:
        return isinstance(value, expected_type)
