# coding: utf-8
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

from __future__ import absolute_import, division, print_function

import json
import sys

from typedjsonrpc.errors import Error, InternalError, get_status_code_from_error_code


class TestInternalError(object):

    def test_from_error_not_serializable(self):
        class NonSerializableObject(object):
            pass
        try:
            e = Exception()
            e.random = NonSerializableObject()
            raise e
        except Exception:
            wrapped_exc = InternalError.from_error(sys.exc_info(), json.JSONEncoder)
            json.dumps(wrapped_exc.as_error_object())

    def test_from_error_serializable(self):
        try:
            e = Exception()
            e.random = {"foo": "bar"}
            raise e
        except Exception:
            wrapped_exc = InternalError.from_error(sys.exc_info(), json.JSONEncoder)
            json.dumps(wrapped_exc.as_error_object())


def test_get_status_code_from_error_code():
    for type_ in [Error] + Error.__subclasses__():
        status_code = get_status_code_from_error_code(type_.code)
        assert type_.status_code == status_code
