from typedjsonrpc.server import *
from werkzeug.debug.tbtools import Traceback
from werkzeug.exceptions import HTTPException
import pytest
import six
import sys

if six.PY3:
    import unittest.mock as mock
else:
    import mock


def _get_fake_traceback():
    try:
        raise Exception()
    except:
        return Traceback(*sys.exc_info())


_FAKE_TRACEBACK = _get_fake_traceback()


class TestDebuggedJsonRpcApplication(object):
    def test_handle_debug(self):
        traceback_id = 5
        debugged_app = DebuggedJsonRpcApplication(None)

        def fake_start_response(body, headers):
            pass
        tb = _FAKE_TRACEBACK
        debugged_app.tracebacks[traceback_id] = tb
        result = debugged_app.handle_debug({}, fake_start_response, traceback_id)
        assert len(result) > 0

    def test_handle_debug_start_response_fails(self):
        traceback_id = 8
        debugged_app = DebuggedJsonRpcApplication(None)

        def fake_start_response(body, headers):
            raise Exception()

        tb = _FAKE_TRACEBACK
        debugged_app.tracebacks[traceback_id] = tb
        mock_error_logger = mock.Mock()
        environ = {"wsgi.errors": mock_error_logger}
        debugged_app.handle_debug(environ, fake_start_response, traceback_id)
        mock_error_logger.write.assert_called_once_with(mock.ANY)

    def test_handle_debug_no_such_traceback(self):
        debugged_app = DebuggedJsonRpcApplication(None)
        with pytest.raises(HTTPException) as excinfo:
            debugged_app.handle_debug(None, None, -1)
        assert excinfo.value.code == 404

    def test_debug_application_debug(self):
        debugged_app = DebuggedJsonRpcApplication(None)
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
