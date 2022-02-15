#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
cytoflow.scripts.split_fcs
---------------------------------

The FCS standard allows multiple datasets to be concatenated into one
FCS file. This script splits them, optionally renaming the resulting
files using the provided FCS metadata
"""

import argparse
import fcsparser
import cytoflow as flow

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fcs_file", help = "FCS file to split")
    parser.add_argument('-n', '--name_metadata', help = "FCS metadata to use as the name")
    parser.add_argument('-d', '--dry', help = "Dry run: say what the program would do but don't do it")
    args = parser.parse_args()
    
    tube_meta = fcsparser.parse(args.fcs_file, meta_data_only = True)

    for i in range(0, 99):
        try:
            op = flow.ImportOp(tubes = [flow.Tube(file = args.fcs_file, conditions = {})],
                               data_set = i)
            ex = op.apply()
        except:
            
    for c in ex.channels:
        m = ex.metadata[c]
        if "voltage" in m:
            print("{0}\t{1}".format(c, m["voltage"]))

if __name__ == '__main__':
    main()