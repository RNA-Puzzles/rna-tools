#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
import argparse

def get_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-v", "--verbose",
                        action="store_true", help="be verbose")
    return parser


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()

    from rna_tools import rna_tools_lib
    print(rna_tools_lib.get_rna_tools_path())
