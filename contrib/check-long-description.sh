#!/bin/sh
# Checks that the long description is PyPI compatible
python setup.py --long-description | rst2html.py --strict > /dev/null
