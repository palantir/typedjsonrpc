from typedjsonrpc.registry import Registry
from typedjsonrpc.server import Server

registry = Registry()
server = Server(registry)


@registry.method()
def add5(x):
    return x + 5


@registry.method()
def fail(x):
    raise Exception(x)


def main():
    server.run("127.0.0.1", 5060)


if __name__ == "__main__":
    main()
