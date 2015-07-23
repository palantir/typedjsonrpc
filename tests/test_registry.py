import json
import pytest

from typedjsonrpc.registry import Registry


def test_register():
    registry = Registry()

    def foo(x):
        return x
    registry.register("bar", foo)
    assert "bar" in registry._name_to_method
    assert registry._name_to_method["bar"] == foo


def test_method():
    registry = Registry()

    @registry.method()
    def foo(x):
        return x
    expected_name = "{}.{}".format(foo.__module__, foo.__name__)
    assert expected_name in registry._name_to_method
    assert registry._name_to_method[expected_name] == foo


def test_dispatch_keyword_args():
    registry = Registry()

    def add(x, y):
        return x + y
    registry.register("add", add)

    class FakeRequest(object):
        def get_data(self):
            return json.dumps({
                "jsonrpc": "2.0",
                "method": "add",
                "params": {
                    "x": 1,
                    "y": 2,
                },
                "id": "bogus",
            })
    fake_request = FakeRequest()
    response = registry.dispatch(fake_request)
    assert response == json.dumps(3)


def test_dispatch_positional_args():
    registry = Registry()

    def add(x, y):
        return x + y
    registry.register("add", add)

    class FakeRequest(object):
        def get_data(self):
            return json.dumps({
                "jsonrpc": "2.0",
                "method": "add",
                "params": [1, 2],
                "id": "bogus",
            })
    fake_request = FakeRequest()
    response = registry.dispatch(fake_request)
    assert response == json.dumps(3)


def test_dispatch_invalid_method():
    registry = Registry()

    class FakeRequest(object):
        def get_data(self):
            return json.dumps({
                "jsonrpc": "2.0",
                "method": "bogus",
                "params": [1, 2],
                "id": "bogus",
            })
    fake_request = FakeRequest()
    with pytest.raises(Exception):
        registry.dispatch(fake_request)
