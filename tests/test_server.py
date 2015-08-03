from typedjsonrpc.registry import Registry
from typedjsonrpc.server import DebuggedJsonRpcApplication, Server
from werkzeug.exceptions import HTTPException
import pytest
import six

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

    def test_handle_debug(self):
        traceback_id = 5
        registry, server, debugged_app = TestDebuggedJsonRpcApplication.get_app()

        def fake_start_response(body, headers):
            pass

        tb = mock.NonCallableMock()
        fake_output = "foo"
        tb.render_full = mock.Mock(return_value=fake_output)
        tb.frames = mock.NonCallableMagicMock()
        registry.tracebacks[traceback_id] = tb
        result = debugged_app.handle_debug({}, fake_start_response, traceback_id)
        tb.render_full.assert_called_once_with(secret=debugged_app.secret,
                                               evalex=debugged_app.evalex)
        assert result == fake_output.encode("utf-8")

    def test_handle_debug_start_response_fails(self):
        traceback_id = 8
        registry, server, debugged_app = TestDebuggedJsonRpcApplication.get_app()

        def fake_start_response(body, headers):
            raise Exception()
        tb = mock.NonCallableMock()
        tb.render_full = mock.Mock()
        tb.frames = mock.NonCallableMagicMock()
        registry.tracebacks[traceback_id] = tb
        mock_error_logger = mock.Mock()
        environ = {"wsgi.errors": mock_error_logger}
        debugged_app.handle_debug(environ, fake_start_response, traceback_id)

    def test_handle_debug_no_such_traceback(self):
        registry, server, debugged_app = TestDebuggedJsonRpcApplication.get_app()
        with pytest.raises(HTTPException) as excinfo:
            debugged_app.handle_debug(None, None, -1)
        assert excinfo.value.code == 404

    def test_debug_application_debug(self):
        registry, server, debugged_app = TestDebuggedJsonRpcApplication.get_app()
        environ = {
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "5060",
            "PATH_INFO": "/debug/1234",
            "REQUEST_METHOD": "POST",
            "wsgi.url_scheme": "http",
            "wsgi.errors": mock.Mock(),
        }
        result = debugged_app.debug_application(environ, None)
        with pytest.raises(HTTPException) as excinfo:
            for _ in result:
                pass
        assert excinfo.value.code == 404

    def test_debug_application_endpoint(self):
        app_return_value = ["foo"]
        mock_app = mock.Mock(return_value=app_return_value)
        mock_app.handle_json_error = mock.Mock(return_value=[])
        debugged_app = DebuggedJsonRpcApplication(mock_app)
        environ = {
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "5060",
            "PATH_INFO": "/api",
            "REQUEST_METHOD": "POST",
            "wsgi.url_scheme": "http",
        }
        result = debugged_app.debug_application(environ, None)
        assert app_return_value == [x for x in result]

    def test_debug_application_endpoint_exception(self):
        mock_app = mock.Mock()
        mock_app.side_effect = Exception()
        handle_json_error_return_value = ["foo"]
        mock_app.handle_json_error = mock.Mock(return_value=handle_json_error_return_value)
        debugged_app = DebuggedJsonRpcApplication(mock_app)
        environ = {
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "5060",
            "PATH_INFO": "/",
            "REQUEST_METHOD": "POST",
            "wsgi.url_scheme": "http",
            "wsgi.errors": mock.Mock(),
        }
        mock_start_response = mock.Mock()
        result = debugged_app.debug_application(environ, mock_start_response)
        assert handle_json_error_return_value == [x for x in result]


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
