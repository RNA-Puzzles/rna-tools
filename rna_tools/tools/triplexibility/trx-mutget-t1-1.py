#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import print_function

import argparse

def get_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)

    #parser.add_argument('-', "--", help="", default="")

    parser.add_argument("-v", "--verbose",
                        action="store_true", help="be verbose")
    parser.add_argument("file", help="", default="") # nargs='+')
    return parser


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()

    aa='x,g,g,c,g,g' # G21
    bb='x,c,g,g,a,u' # C61
    cc='u,c,a,g,u,u' # U80

    csv = open(args.file).read().split('\n')

    for a, b in zip(aa.split(','), bb.split(',')):
         if a != 'x':
             for c in cc.split(','):
                 seq = '2:21' + a + ',6:61' + b + '+80' + c # search for the last column
                 cmd = "rna_pdb_toolsx.py --mutate '" + seq + "' yC_5LJ3_U2U6_core_1st_triplex.pdb > yC_5LJ3_U2U6_core_mdrFx_1-1_" + seq.replace(':', '-').replace(',', '-') + "seq-" + a + b + c + "-rpr.pdb"
                 print(seq)
                 print(cmd)
                 import os
                 os.system(cmd)
