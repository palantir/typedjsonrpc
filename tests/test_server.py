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

from typedjsonrpc.registry import Registry
from typedjsonrpc.server import current_request, DebuggedJsonRpcApplication, Server, Response
from werkzeug.exceptions import HTTPException
import pytest
import six
import werkzeug.debug

if six.PY3:
    import unittest.mock as mock
else:
    import mock


class TestDebuggedJsonRpcApplication(object):
    @staticmethod
    def get_app():
        registry = Registry()
        server = Server(registry)
        debugged_app = DebuggedJsonRpcApplication(server)
        return registry, server, debugged_app

    def test_handle_debug_no_such_traceback(self):
        registry, server, debugged_app = TestDebuggedJsonRpcApplication.get_app()
        with pytest.raises(HTTPException) as excinfo:
            debugged_app.handle_debug(None, None, -1)
        assert excinfo.value.code == 404

    def test_handle_debug_response_called(self):
        registry, server, debugged_app = TestDebuggedJsonRpcApplication.get_app()
        mock_traceback = mock.Mock()
        mock_traceback.render_full = mock.Mock(return_value="")
        mock_traceback.frames = mock.NonCallableMagicMock()
        registry.tracebacks[1234] = mock_traceback
        start_response = mock.Mock()
        environ = {
             "SERVER_NAME": "localhost",
             "SERVER_PORT": "5060",
             "PATH_INFO": "/api",
             "REQUEST_METHOD": "POST",
             "wsgi.url_scheme": "http",
        }
        debugged_app.handle_debug(environ, start_response, 1234)

    @mock.patch("typedjsonrpc.server.DebuggedJsonRpcApplication.handle_debug",
                mock.Mock(return_value=["foo"]))
    def test_debug_application_debug_endpoint(self):
        registry, server, debugged_app = TestDebuggedJsonRpcApplication.get_app()
        environ = {
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "5060",
            "PATH_INFO": "/debug/1234",
            "REQUEST_METHOD": "POST",
            "wsgi.url_scheme": "http",
        }
        start_response = mock.Mock()
        assert ["foo"] == debugged_app.debug_application(environ, start_response)
        assert DebuggedJsonRpcApplication.handle_debug.called

    @mock.patch("werkzeug.debug.DebuggedApplication.debug_application",
                mock.Mock(return_value=["foo"]))
    def test_debug_application_normal_endpoint(self):
        registry, server, debugged_app = TestDebuggedJsonRpcApplication.get_app()
        environ = {
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "5060",
            "PATH_INFO": "/api",
            "REQUEST_METHOD": "POST",
            "wsgi.url_scheme": "http",
        }
        start_response = mock.NonCallableMock()
        result = debugged_app.debug_application(environ, start_response)
        assert result == ["foo"]
        assert werkzeug.debug.DebuggedApplication.debug_application.called


class TestServer(object):

    def test_wsgi_app_invalid_endpoint(self):
        environ = {
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "5060",
            "PATH_INFO": "/bogus",
            "REQUEST_METHOD": "POST",
            "wsgi.url_scheme": "http",
        }
        mock_registry = mock.Mock()
        server = Server(mock_registry, "/foo")
        with pytest.raises(HTTPException) as excinfo:
            server(environ, None)
        assert excinfo.value.code == 404

    def test_wsgi_app_dispatch(self):
        environ = {
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "5060",
            "PATH_INFO": "/foo",
            "REQUEST_METHOD": "POST",
            "wsgi.url_scheme": "http",
        }
        mock_registry = mock.Mock()
        mock_registry.dispatch.return_value = "foo"
        server = Server(mock_registry, "/foo")
        mock_start_response = mock.Mock()
        server(environ, mock_start_response)
        mock_registry.dispatch.assert_called_once_with(mock.ANY)

    def test_before_first_request_funcs(self):
        environ = {
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "5060",
            "PATH_INFO": "/foo",
            "REQUEST_METHOD": "POST",
            "wsgi.url_scheme": "http",
        }
        mock_registry = mock.Mock()
        mock_registry.dispatch.return_value = "foo"

        mock_start = mock.Mock()
        mock_start.return_value(None)
        server = Server(mock_registry, "/foo")
        server.register_before_first_request(mock_start)

        mock_start_response = mock.Mock()
        server(environ, mock_start_response)
        server(environ, mock_start_response)

        mock_start.assert_called_once_with()


class TestCurrentRequest(object):
    def test_current_request_set(self):
        registry = Registry()
        server = Server(registry)

        def fake_dispatch_request(request):
            assert current_request == request
            return Response()
        server._dispatch_request = fake_dispatch_request
        environ = {
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "5060",
            "PATH_INFO": "/foo",
            "REQUEST_METHOD": "POST",
            "wsgi.url_scheme": "http",
        }
        mock_start_response = mock.Mock()
        server(environ, mock_start_response)

    def test_current_request_passed_to_registry(self):
        registry = Registry()
        server = Server(registry)

        def fake_dispatch(request):
            assert current_request == request
            return Response()
        registry.dispatch = fake_dispatch
        environ = {
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "5060",
            "PATH_INFO": "/api",
            "REQUEST_METHOD": "POST",
            "wsgi.url_scheme": "http",
        }
        mock_start_response = mock.Mock()
        server(environ, mock_start_response)
