"""Contains the Werkzeug server for debugging and WSGI compatibility."""
from __future__ import absolute_import, print_function

import json

from werkzeug.debug import DebuggedApplication
from werkzeug.debug.tbtools import get_current_traceback
from werkzeug.exceptions import abort
from werkzeug.serving import run_simple
from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Request, Response

__all__ = ["Server", "DebuggedJsonRpcApplication"]


DEFAULT_API_ENDPOINT_NAME = "/api"


class Server(object):
    """A basic WSGI-compatible server for typedjsonrpc endpoints."""

    def __init__(self, registry, endpoint=DEFAULT_API_ENDPOINT_NAME):
        """
        :param typedjsonrpc.registry.Registry registry: The jsonrpc registry to use
        :param str endpoint (optional): The endpoint to publish jsonrpc endpoints. Default "/api".
        """
        self._registry = registry
        self.endpoint = endpoint
        self._url_map = Map([Rule(endpoint, endpoint=self.endpoint)])

    def _dispatch_request(self, request):
        adapter = self._url_map.bind_to_environ(request.environ)
        endpoint, _ = adapter.match()
        if endpoint == self.endpoint:
            json_output = self._registry.dispatch(request)
            return Response(json_output, mimetype="application/json")
        else:
            abort(500)

    def wsgi_app(self, environ, start_response):
        """A basic WSGI app"""
        request = Request(environ)
        response = self._dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def run(self, host, port, **options):
        """For debugging purposes, you can run this as a standalone server"""
        debugged = DebuggedJsonRpcApplication(self, evalex=True)
        run_simple(host, port, debugged, use_reloader=True, **options)

    @staticmethod
    def handle_json_error(environ, start_response, traceback):
        """Handles a json error specially by returning the id which links to the failure"""
        response = Response(json.dumps({"traceback_id": traceback.id}), mimetype="application/json")
        return response(environ, start_response)


class DebuggedJsonRpcApplication(DebuggedApplication):
    """A jsonrpc-specific debugged application.

    This differs from DebuggedApplication since the normal debugger assumes you
    are hitting the endpoint from a web browser.

    A returned response will be JSON of the form: {"traceback_id": <id>} which
    you can use to hit the endpoint http://<host>:<port>/debug/<traceback_id>.

    NOTE: This should never be used in production because the user gets shell
    access in debug mode.

    """
    def __init__(self, app, **kwargs):
        """
        :param app: The wsgi application to be debugged
        :param kwargs: The arguments to pass to the DebuggedApplication
        """
        super(DebuggedJsonRpcApplication, self).__init__(app, **kwargs)
        self._debug_map = Map([Rule("/debug/<int:traceback_id>", endpoint="debug")])

    def debug_application(self, environ, start_response):
        """Run the application and preserve the traceback frames.

        :param environ:
        :param start_response:
        """
        app_iter = None
        adapter = self._debug_map.bind_to_environ(environ)
        if adapter.test():
            _, args = adapter.match()
            yield self.handle_debug(environ, start_response, args["traceback_id"])
        else:
            try:
                app_iter = self.app(environ, start_response)
                for item in app_iter:
                    yield item
                if hasattr(app_iter, 'close'):
                    app_iter.close()
            except Exception:  # pylint: disable=broad-except
                if hasattr(app_iter, 'close'):
                    app_iter.close()
                traceback = get_current_traceback(skip=1,
                                                  show_hidden_frames=self.show_hidden_frames,
                                                  ignore_system_exceptions=True)
                for frame in traceback.frames:
                    self.frames[frame.id] = frame
                self.tracebacks[traceback.id] = traceback
                error_iter = self.app.handle_json_error(environ, start_response, traceback)
                for item in error_iter:
                    yield item
                traceback.log(environ['wsgi.errors'])

    def handle_debug(self, environ, start_response, traceback_id):
        """Handles the debug endpoint for inspecting previous errors.

        :param environ:
        :param start_response:
        :param int traceback_id: The id of the traceback to inspect
        :return:
        """
        if traceback_id not in self.tracebacks:
            abort(404)
        traceback = self.tracebacks[traceback_id]
        try:
            start_response('500 INTERNAL SERVER ERROR', [
                ('Content-Type', 'text/html; charset=utf-8'),
                # Disable Chrome's XSS protection, the debug
                # output can cause false-positives.
                ('X-XSS-Protection', '0'),
            ])
        except Exception:  # pylint: disable=broad-except
            # if we end up here there has been output but an error
            # occurred.  in that situation we can do nothing fancy any
            # more, better log something into the error log and fall
            # back gracefully.
            environ['wsgi.errors'].write(
                'Debugging middleware caught exception in streamed '
                'response at a point where response headers were already '
                'sent.\n')
        else:
            rendered = traceback.render_full(evalex=self.evalex, secret=self.secret)
            return rendered.encode('utf-8', 'replace')
