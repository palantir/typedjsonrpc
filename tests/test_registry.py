import json
import pytest

from typedjsonrpc.errors import (InvalidParamsError, InvalidReturnTypeError, InvalidRequestError,
                                 MethodNotFoundError, ParseError)
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

    @registry.method(returns=str, x=str)
    def foo(x):
        return x
    expected_name = "{}.{}".format(foo.__module__, foo.__name__)
    assert expected_name in registry._name_to_method
    assert registry._name_to_method[expected_name] == foo


def test_method_correct_argtypes():
    registry = Registry()

    @registry.method(returns=str, some_text=str, some_number=int)
    def foo(some_text, some_number):
        return some_text + str(some_number)
    assert foo("Hello", 5) == "Hello5"
    assert foo(some_text="Hello", some_number=5) == "Hello5"
    assert foo("Hello", some_number=5) == "Hello5"
    assert foo(some_number=5, some_text="Hello") == "Hello5"

    @registry.method(returns=str)
    def bar():
        return "Works"
    assert bar() == "Works"

    @registry.method(returns=str, some_text=str, some_number=int)
    def stuff(some_number, some_text):
        return str(some_number) + some_text
    assert stuff(42, "Answer") == "42Answer"


def test_method_args():
    registry = Registry()

    @registry.method(returns=str, some_text=str, some_number=int)
    def foo(some_text, some_number, *args):
        return some_text + str(some_number) + str(args)
    assert foo("Hi", 5, 6, "Test") == "Hi5(6, 'Test')"

    @registry.method(returns=str, some_text=str, some_number=int)
    def bar(some_text, some_number, *args, **kwargs):
        return some_text + str(some_number) + str(args) + str(kwargs)
    assert bar("Hi", 5, "foo", bla=6, stuff="Test") == "Hi5('foo',){'stuff': 'Test', 'bla': 6}"
    with pytest.raises(InvalidParamsError):
        bar("Hi", test=7)


def test_method_defaults():
    registry = Registry()

    @registry.method(returns=str, some_number=int, some_text=str)
    def foo(some_number, some_text="Test"):
        return some_text
    assert foo(5) == "Test"
    assert foo(5, "Hello") == "Hello"


def test_method_wrong_type_declarations():
    registry = Registry()

    with pytest.raises(Exception):
        @registry.method(returns=str, some_text=str, some_number=int)
        def foo(some_text, some_stuff):
            return some_text + some_stuff


def test_method_wrong_argument_order():
    registry = Registry()

    @registry.method(returns=str, some_text=str, some_number=int)
    def foo(some_text, some_number):
        return some_text + str(some_number)
    assert foo("Answer", 42) == "Answer42"
    with pytest.raises(InvalidParamsError):
        foo(42, "Answer")


def test_method_wrong_return_type():
    registry = Registry()

    @registry.method(returns=str, some_number=int)
    def foo(some_number):
        return some_number
    with pytest.raises(InvalidReturnTypeError):
        foo(5)


def test_method_no_return_type():
    registry = Registry()

    with pytest.raises(Exception):
        @registry.method(some_number=int)
        def foo(some_number):
            return some_number


def test_method_return_type_none():
    registry = Registry()

    @registry.method(returns=None)
    def foo():
        pass
    foo()

    @registry.method(returns=type(None))
    def fun():
        pass
    fun()

    @registry.method(returns=type(None), some_text=str)
    def bar(some_text):
        return some_text
    with pytest.raises(InvalidReturnTypeError):
        bar("Hello")

    @registry.method(returns=None, some_number=int)
    def stuff(some_number):
        return 2 * some_number
    with pytest.raises(InvalidReturnTypeError):
        stuff(21)


def test_method_parameter_named_returns():
    registry = Registry()

    with pytest.raises(Exception):
        @registry.method(returns=str, some_number=int)
        def foo(some_number, returns):
            return str(some_number) + returns


class TestDispatch(object):
    @staticmethod
    def _create_fake_request(data):
        class FakeRequest(object):
            def get_data(self):
                return json.dumps(data)
        return FakeRequest()

    def test_keyword_args(self):
        registry = Registry()

        def add(x, y):
            return x + y
        registry.register("add", add)

        fake_request = self._create_fake_request({
            "jsonrpc": "2.0",
            "method": "add",
            "params": {
                "x": 1,
                "y": 2,
            },
            "id": "bogus",
        })
        response = registry.dispatch(fake_request)
        assert response == json.dumps({
            "jsonrpc": "2.0",
            "id": "bogus",
            "result": 3
        })

    def test_positional_args(self):
        registry = Registry()

        def add(x, y):
            return x + y
        registry.register("add", add)

        fake_request = self._create_fake_request({
            "jsonrpc": "2.0",
            "method": "add",
            "params": [1, 2],
            "id": "bogus",
        })
        response = registry.dispatch(fake_request)
        assert response == json.dumps({
            "jsonrpc": "2.0",
            "id": "bogus",
            "result": 3
        })

    def test_invalid_method(self):
        registry = Registry()

        fake_request = self._create_fake_request({
            "jsonrpc": "2.0",
            "method": "bogus",
            "params": [1, 2],
            "id": "bogus",
        })
        with pytest.raises(MethodNotFoundError):
            registry.dispatch(fake_request)

    def test_invalid_params(self):
        registry = Registry()

        @registry.method(returns=None)
        def foo():
            pass

        fake_request = self._create_fake_request({
            "jsonrpc": "2.0",
            "method": "test_registry.foo",
            "params": "Hello world",
            "id": 42,
        })
        with pytest.raises(InvalidRequestError):
            registry.dispatch(fake_request)

    def test_invalid_request_wrong_jsonrpc(self):
        registry = Registry()

        @registry.method(returns=None)
        def bogus(*args):
            print(args)

        fake_request = self._create_fake_request({
            "jsonrpc": "1.0",
            "method": "test_registry.bogus",
            "params": [1, 2],
        })
        with pytest.raises(InvalidRequestError):
            registry.dispatch(fake_request)

    def test_invalid_request_no_method(self):
        registry = Registry()

        fake_request = self._create_fake_request({
            "jsonrpc": "2.0",
            "params": [1, 2],
            "id": "test",
        })
        with pytest.raises(InvalidRequestError):
            registry.dispatch(fake_request)

    def test_invalid_request_float_id(self):
        registry = Registry()

        @registry.method(returns=None)
        def bogus(*args):
            print(args)

        fake_request = self._create_fake_request({
            "jsonrpc": "2.0",
            "method": "test_registry.bogus",
            "params": [1, 2],
            "id": 1.0,
        })
        with pytest.raises(InvalidRequestError):
            registry.dispatch(fake_request)

    def test_invalid_request_no_jsonrpc(self):
        registry = Registry()

        @registry.method(returns=None)
        def bogus(*args):
            print(args)

        fake_request = self._create_fake_request({
            "method": "test_registry.bogus",
            "params": [1, 2],
        })
        with pytest.raises(InvalidRequestError):
            registry.dispatch(fake_request)

    def test_invalid_json(self):
        registry = Registry()

        class FakeRequest(object):
            def get_data(self):
                return '{ "jsonrpc": "2.0", "method":, "id":]'

        fake_request = FakeRequest()
        with pytest.raises(ParseError):
            registry.dispatch(fake_request)

    def test_id(self):
        registry = Registry()

        @registry.method(returns=int)
        def foo():
            return 42

        fake_request0 = self._create_fake_request({
            "jsonrpc": "2.0",
            "method": "test_registry.foo",
        })
        fake_request1 = self._create_fake_request({
            "jsonrpc": "2.0",
            "method": "test_registry.foo",
            "id": 1
        })
        fake_request2 = self._create_fake_request({
            "jsonrpc": "2.0",
            "method": "test_registry.foo",
            "id": None
        })
        fake_request3 = self._create_fake_request({
            "jsonrpc": "2.0",
            "method": "test_registry.foo",
            "id": [1, 2, 3]
        })
        fake_request4 = self._create_fake_request({
            "jsonrpc": "2.0",
            "method": "test_registry.foo",
            "id": 4.0
        })

        assert registry.dispatch(fake_request0) is None
        assert json.loads(registry.dispatch(fake_request1))["result"] == 42
        with pytest.raises(InvalidRequestError):
            registry.dispatch(fake_request2)
        with pytest.raises(InvalidRequestError):
            registry.dispatch(fake_request3)
        with pytest.raises(InvalidRequestError):
            registry.dispatch(fake_request4)
