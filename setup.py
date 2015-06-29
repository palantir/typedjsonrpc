"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

import versioneer

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "DESCRIPTION.rst"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="typedjsonrpc",

    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),

    description="A typed decorator-based json-rpc library for Python",
    long_description=long_description,

    url="https://github.com/palantir/typedjsonrpc",

    author="Michael Nazario",
    author_email="mnazario@palantir.com",

    license="MIT",

    classifiers=[
        "Development Status :: 3 - Alpha",

        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP",

        "License :: OSI Approved :: MIT License",

        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
    ],

    keywords="jsonrpc json-rpc rpc",

    packages=find_packages(exclude=["contrib", "docs", "tests*"]),

    install_requires=[],

    extras_require={},
)
