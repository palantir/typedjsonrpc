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

=============
Release Notes
=============

0.3.0
-----
This is a small update to better handle JSON encoding errors.

Bugfixes
^^^^^^^^
* Any exceptions thrown by a custom :class:`json.JSONEncoder` will be reencoded after the exception
  has been thrown. JSON-RPC will not return a response if the custom encoder cannot encode the
  exception.

0.2.0
-----
This is a small update from the last release based on usage.

Features
^^^^^^^^
* Added ability to access the current request in method call
* Allowed more flexibility in JSON serialization

Bugfixes
^^^^^^^^
* Exceptions which are not JSON-serializable are now converted to strings using :func:`repr` rather
  than failing serialization

Breaking changes
^^^^^^^^^^^^^^^^
* :attr:`typedjsonrpc.registry.Registry.json_encoder` and
  :attr:`typedjsonrpc.registry.Registry.json_decoder` are now instances rather than class objects

0.1.0
-----
Initial Release
