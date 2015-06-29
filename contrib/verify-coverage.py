#!/usr/bin/env python

import sys
from xml.etree import ElementTree


def main(min_percentage):
    tree = ElementTree.parse("build/coverage-results/coverage.xml")
    actual_percentage = float(tree.getroot().attrib["line-rate"])
    if actual_percentage < min_percentage:
        print("Total coverage does not meet minimum:"
              " Expected: {}, Actual: {}:".format(min_percentage, actual_percentage))
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: {} <decimal percent min coverage>".format(sys.argv[0]))
    min_percentage = float(sys.argv[1])
    main(min_percentage)
