from typedjsonrpc.registry import Registry
from typedjsonrpc.server import Server

registry = Registry()
server = Server(registry)


@registry.method(returns=int, x=int)
def add5(x):
    return x + 5


@registry.method(returns=None, x=str)
def fail(x):
    raise Exception(x)


def main():
    server.run("127.0.0.1", 5060)


if __name__ == "__main__":
    main()
