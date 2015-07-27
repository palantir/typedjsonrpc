# typedjsonrpc 
typedjsonrpc is a typed decorator-based json-rpc library for Python. It is influenced by [Flask JSON-RPC](https://github.com/cenobites/flask-jsonrpc) but has some key differences: 

typedjsonrpc...
* supports floats
* allows return type checking
* focuses on easy debugging

## Using typedjsonrpc
### Installation
Clone the repository and install typedjsonrpc:
```
$ git clone https://github.com/palantir/typedjsonrpc.git
$ cd typedjsonrpc
$ pip install .
```
### Project setup
To include typedjsonrpc in your project, use:
```
from typedjsonrpc.registry import Registry
from typedjsonrpc.server import Server

registry = Registry()
server = Server(registry)
``` 
The registry will keep track of the methods that are available for json-rpc - whenever you annotate a method it will be added to the registry. `Server` is a uwsgi compatible app that handles the requests. It has a development mode that can be run using `server.run(host, port)`.
### Example usage
Annotate your methods to make them accessible and provide type information:
```
@registry.method(returns=int, a=int, b=int)
def add(a, b):
    return a + b

@registry.method(returns=str, a=str, b=str)
def concat(a, b):
    return a + b
```
The return type *has* to be declared using the `returns` keyword. For methods that don't return anything, you can use either `type(None)` or just `None`:
```
@registry.method(returns=type(None), a=str)
def foo(a):
    print(a)
    
@registry.method(returns=None, a=int)
def bar(a):
    print(5 * a)
```

You can use any of the basic json types:

|json type | Python type |
|----------|-------------|
|string    | basestring (Python 2), str (Python 3) |
|number    | int, float  |
|null      | None        |
|boolean   | bool        |
|array     | list        |
|object    | dict        |

Your functions may also accept `*args` and `**kwargs`, but you cannot declare their types. So the correct way to use these would be:
```
@registry.method(a=str)
def foo(a, *args, **kwargs):
    return a + str(args) + str(kwargs)
```

To check that everything is running properly, try (assuming `add` is declared in your main module):
```
$ curl -XPOST http://localhost:3031/api -d '{"jsonrpc": "2.0", "method":"__main__.add","params": {"a": 5, "b": 7}, "id": "foo"}'
12
```
Passing any non-integer arguments into `add` will raise a `TypeError`.

## Dependencies 
* werkzeug
* wrapt
