#!/usr/bin/env python
# coding: utf-8
#
# Copyright 2015 Palantir Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import absolute_import, division, print_function

import versioneer

from codecs import open
from os import path
from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="typedjsonrpc",

    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),

    description="A typed decorator-based JSON-RPC library for Python",
    long_description=long_description,

    url="https://github.com/palantir/typedjsonrpc",

    author="Michael Nazario",
    author_email="mnazario@palantir.com",

    maintainer="Michael Nazario",
    maintainer_email="mnazario@palantir.com",

    license="Apache License 2.0",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",

        "License :: OSI Approved :: Apache Software License",

        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
    ],

    keywords="jsonrpc json-rpc rpc",

    packages=find_packages(where=here, exclude=["contrib", "docs", "tests*"]),

    install_requires=[
        "six>=1.0.0,<2.0.0",
        "werkzeug>=0.10.0,<0.11.0",
        "wrapt>=1.10.0,<2.0.0",
    ],
)
