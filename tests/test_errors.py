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

import json
import sys

from typedjsonrpc.errors import InternalError


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
