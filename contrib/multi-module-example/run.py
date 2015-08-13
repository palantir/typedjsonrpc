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

"""Multi-module example

This multi-module example showcases how a more complicated JSON-RPC server can be set up. You can
have namespacing of your different JSON-RPC methods based on their module name. The method will have
the form ``<module_name>.<method_name>``.

To run this example, run:
.. code-block:: bash

    $ cd /path/to/typedjsonrpc/contrib/multi-module-example
    $ python -m run.py

If you were to make a request to "rpc.describe", you'll see that all of the registered methods have
the form::

    typedjsonrpc_example.<module_name>.method_name

This will work for any arbitrary module structure which you use. All you have to do is to ensure
that you import your submodules in the correct order. In ``typedjsonrpc_example.__init__.py`` a
``Server`` object is created and is referenced in submodules. Those submodules are then imported
here before the server is started. This completes the circular reference.

If you choose to call ``typedjsonrpc_example.invalid.raise_error`` through JSON-RPC, you'll discover
that typedjsonrpc gives you a ``debug_url`` field in the error message. This is a link to the
Werkzeug debugger at ``http://<host>:<port>/<debug_url>``.
"""
from typedjsonrpc_example import server


# Modules must be registered before running the server
if __name__ == "__main__":
    server.run("0.0.0.0", 3031)
