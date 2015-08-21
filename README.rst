..
    Copyright 2015 Palantir Technologies, Inc.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

============
typedjsonrpc
============
.. image:: https://img.shields.io/pypi/status/typedjsonrpc.svg
     :target: https://img.shields.io/pypi/status/typedjsonrpc

.. image:: https://img.shields.io/pypi/l/typedjsonrpc.svg
     :target: https://img.shields.io/pypi/l/typedjsonrpc

.. image:: https://img.shields.io/pypi/pyversions/typedjsonrpc.svg
     :target: https://img.shields.io/pypi/pyversions/typedjsonrpc

.. image:: https://img.shields.io/pypi/wheel/typedjsonrpc.svg
     :target: https://img.shields.io/pypi/wheel/typedjsonrpc

.. image:: https://badge.fury.io/py/typedjsonrpc.svg
     :target: http://badge.fury.io/py/typedjsonrpc

.. image:: https://travis-ci.org/palantir/typedjsonrpc.svg
     :target: https://travis-ci.org/palantir/typedjsonrpc

typedjsonrpc is a decorator-based `JSON-RPC <http://www.jsonrpc.org/specification>`_ library for
Python that exposes parameter and return types. It is influenced by
`Flask JSON-RPC <https://github.com/cenobites/flask-jsonrpc>`_ but has some key differences:

typedjsonrpc...

* allows return type checking
* focuses on easy debugging

These docs are also available on `Read the Docs <http://typedjsonrpc.readthedocs.org>`_.

Using typedjsonrpc
==================
Installation
------------
Use pip to install typedjsonrpc:

.. code-block:: bash

    $ pip install typedjsonrpc

Project setup
-------------
To include typedjsonrpc in your project, use:

.. code-block:: python

    from typedjsonrpc.registry import Registry
    from typedjsonrpc.server import Server

    registry = Registry()
    server = Server(registry)

The registry will keep track of methods that are available for JSON-RPC. Whenever you annotate
a method, it will be added to the registry. You can always use the method ``rpc.describe()`` to get
a description of all available methods. ``Server`` is a
`WSGI <http://wsgi.readthedocs.org/en/latest/>`_ compatible app that handles requests. ``Server``
also has a development mode that can be run using ``server.run(host, port)``.

Example usage
-------------
Annotate your methods to make them accessible and provide type information:

.. code-block:: python

    @registry.method(returns=int, a=int, b=int)
    def add(a, b):
        return a + b

    @registry.method(returns=str, a=str, b=str)
    def concat(a, b):
        return a + b

The return type *has* to be declared using the ``returns`` keyword. For methods that don't return
anything, you can use either ``type(None)`` or just ``None``:

.. code-block:: python

    @registry.method(returns=type(None), a=str)
    def foo(a):
        print(a)

    @registry.method(returns=None, a=int)
    def bar(a):
        print(5 * a)

You can use any of the basic JSON types:

==========  =====================================
JSON type   Python type
==========  =====================================
string      basestring (Python 2), str (Python 3)
number      int, float
null        None
boolean     bool
array       list
object      dict
==========  =====================================

Your functions may also accept ``*args`` and ``**kwargs``, but you cannot declare their types. So
the correct way to use these would be:

.. code-block:: python

    @registry.method(a=str)
    def foo(a, *args, **kwargs):
        return a + str(args) + str(kwargs)

To check that everything is running properly, try (assuming ``add`` is declared in your main
module):

.. code-block:: bash

    $ curl -XPOST http://<host>:<port>/api -d @- <<EOF
    {
        "jsonrpc": "2.0",
        "method": "__main__.add",
        "params": {
            "a": 5,
            "b": 7
        },
        "id": "foo"
    }
    EOF

    {
        "jsonrpc": "2.0",
        "id": "foo",
        "result": 12
    }

Passing any non-integer arguments into ``add`` will raise a ``InvalidParamsError``.

Batching
--------
You can send a list of JSON-RPC request objects as one request and will receive a list of JSON-RPC
response objects in return. These response objects can be mapped back to the request objects using
the ``id``. Here's an example of calling the ``add`` method with two sets of parameters:

.. code-block:: bash

    $ curl -XPOST http://<host>:<port>/api -d @- <<EOF
    [
        {
            "jsonrpc": "2.0",
            "method": "__main__.add",
            "params": {
                "a": 5,
                "b": 7
            },
            "id": "foo"
        }, {
            "jsonrpc": "2.0",
            "method": "__main__.add",
            "params": {
                "a": 42,
                "b": 1337
            },
            "id": "bar"
        }
    ]
    EOF

    [
        {
            "jsonrpc": "2.0",
            "id": "foo",
            "result": 12
        }, {
            "jsonrpc": "2.0",
            "id": "bar",
            "result": 1379
        }
    ]

Debugging
---------
If you create the registry with the parameter ``debug=True``, you'll be able to use
`werkzeug's debugger <http://werkzeug.pocoo.org/docs/0.10/debug/>`_. In that case, if there is an
error during execution - e.g. you tried to use a string as one of the parameters for ``add`` - the
response will contain an error object with a ``debug_url``:

.. code-block:: bash

    $ curl -XPOST http://<host>:<port>/api -d @- <<EOF
    {
        "jsonrpc": "2.0",
        "method": "__main__.add",
        "params": {
            "a": 42,
            "b": "hello"
        },
        "id": "bar"
    }
    EOF

    {
        "jsonrpc": "2.0",
        "id": "bar",
        "error": {
            "message": "Invalid params",
            "code": -32602,
            "data": {
                "message": "Value 'hello' for parameter 'b' is not of expected type <type 'int'>.",
                "debug_url": "/debug/1234567890"
            }
        }
    }

This tells you to find the traceback interpreter at ``<host>:<port>/debug/1234567890``.

Additional features
===================

Customizing type serialization
------------------------------
If you would like to serialize custom types, you can set the ``json_encoder`` and ``json_decoder``
attributes on ``Server`` to your own custom :class:`json.JSONEncoder` and :class:`json.JSONDecoder`
instance. By default, we use the default encoder and decoder.

Adding hooks before the first request
-------------------------------------
You can add functions to run before the first request is called. This can be useful for some
special setup you need for your WSGI app. For example, you can register a function to print
debugging information before your first request:

.. code-block:: python

    import datetime

    from typedjsonrpc.registry import Registry
    from typedjsonrpc.server import Server

    registry = Registry()
    server = Server(registry)

    def print_time():
        now = datetime.datetime.now()
        print("Handling first request at: {}".format(now))

    server.register_before_first_request(print_time)

Accessing the HTTP request from JSON-RPC methods
------------------------------------------------
In some situations, you may want to access the HTTP request from your JSON-RPC method. For example,
you could need to perform logic based on headers in the request. In the :mod:`typedjsonrpc.server`
module, there is a special :attr:`typedjsonrpc.server.current_request` attribute which allows you to
access the HTTP request which was used to call the current method.

.. warning::

    ``current_request`` is implemented as a thread-local. If you attempt to call
    ``Server.wsgi_app`` from ``Registry.method``, then ``current_request`` *will be overriden in*
    *that thread*.

Example:

.. code-block:: python

    from typedjsonrpc.server import current_request

    @registry.method(returns=list)
    def get_headers():
        return list(current_request.headers)
