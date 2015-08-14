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

"""Single module example

This basic example showcases using a single module for typedjsonrpc. It registers each method in the
module which this process was run.

To run this example, run:
.. code-block:: bash

    $ cd /path/to/typedjsonrpc/contrib/single-module-example
    $ python example.py

If you were to make a request to "rpc.describe", you'll see that all of the registered methods have
the form::

    __main__.method_name

This is because the module which is invoked as the entry point into Python is referred to as
``__main__``.

If you choose to call ``__main__.raise_error`` through JSON-RPC, you'll discover that typedjsonrpc
gives you a ``debug_url`` field in the error message. This is a link to the Werkzeug debugger at
``http://<host>:<port>/<debug_url>``.
"""
import six
from typedjsonrpc.registry import Registry
from typedjsonrpc.server import Server


# For Python 2 and 3 compatibility
STRING_TYPE = six.string_types[0]

registry = Registry()
server = Server(registry)


@registry.method(returns=int, a=int, b=int)
def add(a, b):
    return a + b


@registry.method(returns=int, a=int, b=int)
def add_with_docstring(a, b):
    """Adds two numbers together.

    :param a: Left-hand side number
    :type a: int
    :param b: Right-hand side number
    :type b: int
    :return: The sum
    :rtype: int
    """
    return add(a, b)


@registry.method(returns=float, a=float, b=float)
def add_floats(a, b):
    return a + b


@registry.method(returns=None, message=STRING_TYPE)
def raise_error(message):
    raise Exception(message)


@registry.method(returns=STRING_TYPE, message=STRING_TYPE, repetitions=int)
def shout(message, repetitions):
    return "! ".join([message[:]] * repetitions) + "!"


# Run the server after registering methods
server.run("localhost", 3031)
