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

from __future__ import print_function

from . import registry


@registry.method(returns=dict, data=list)
def histogram(data):
    """Returns a histogram of your data.

    :param data: The data to histogram
    :type data: list[object]
    :return: The histogram
    :rtype: dict[object, int]
    """
    ret = {}
    for datum in data:
        if datum in ret:
            ret[datum] += 1
        else:
            ret[datum] = 1
    return ret


@registry.method(returns=bool, data=list)
def all_true(data):
    """Checks if all of the elements are True.

    :param data: The list of boolean values
    :type data: list[bool]
    :return: True if all elements in the list are true
    :rtype: bool
    """
    return all(data)


@registry.method(returns=float, data=list)
def mean(data):
    """Returns the mean of the data as a float

    :param data: The list of boolean values
    :type data: list[int | float]
    :return: The mean of the list
    :rtype: float
    """
    total = float(sum(data))
    return total / len(data)


@registry.method(returns=None, data=dict)
def print_data(data):
    """Prints object key-value pairs in a custom format

    :param data: The dict to print
    :type data: dict
    :rtype: None
    """
    print(", ".join(["{}=>{}".format(key, value) for key, value in data]))
