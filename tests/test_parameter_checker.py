import pytest
import typedjsonrpc.parameter_checker as parameter_checker

from typedjsonrpc.errors import InvalidParamsError


def test_list():
    def foo(a, b, c="baz"):
        pass

    with pytest.raises(InvalidParamsError):
        parameter_checker.validate_params_match(foo, ["foo"])
    parameter_checker.validate_params_match(foo, ["foo", "bar"])

    with pytest.raises(InvalidParamsError):
        parameter_checker.validate_params_match(foo, ["foo", "bar", "bop", 42])


def test_varargs():
    def foo(a, b="foo", *varargs):
        pass

    with pytest.raises(InvalidParamsError):
        parameter_checker.validate_params_match(foo, [])
    parameter_checker.validate_params_match(foo, ["foo", "bar"])
    parameter_checker.validate_params_match(foo, ["foo", "bar", 42])


def test_dict():
    def foo(a, b, c="baz"):
        pass

    with pytest.raises(InvalidParamsError):
        parameter_checker.validate_params_match(foo, {"a": "foo"})
    parameter_checker.validate_params_match(foo, {"a": "foo", "b": "bar"})

    with pytest.raises(InvalidParamsError):
        parameter_checker.validate_params_match(foo, {"a": "foo", "b": "bar", "c": "bop", "d": 42})

    with pytest.raises(InvalidParamsError):
        parameter_checker.validate_params_match(foo, {"a": "foo", "c": "bar"})


def test_kwargs():
    def foo(a, b, c="baz", **kwargs):
        pass

    with pytest.raises(InvalidParamsError):
        parameter_checker.validate_params_match(foo, {"a": "foo"})
    parameter_checker.validate_params_match(foo, {"a": "foo", "b": "bar"})

    parameter_checker.validate_params_match(foo, {"a": "foo", "b": "bar", "d": 42})

    with pytest.raises(InvalidParamsError):
        parameter_checker.validate_params_match(foo, {"a": "foo", "c": "bar"})


def test_no_defaults():
    def foo(a):
        pass
    with pytest.raises(InvalidParamsError):
        parameter_checker.validate_params_match(foo, [])
    parameter_checker.validate_params_match(foo, ["bar"])
    with pytest.raises(InvalidParamsError):
        parameter_checker.validate_params_match(foo, ["bar", "baz"])

    with pytest.raises(InvalidParamsError):
        parameter_checker.validate_params_match(foo, {})
    parameter_checker.validate_params_match(foo, {"a": "bar"})
    with pytest.raises(InvalidParamsError):
        parameter_checker.validate_params_match(foo, {"a": "bar", "b": "baz"})
