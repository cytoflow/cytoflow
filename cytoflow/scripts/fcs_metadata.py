#!/usr/bin/env python3.4
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

'''
cytoflow.scripts.fcs_metadata
---------------------------------
'''

import argparse
import fcsparser

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fcs_file", help = "FCS file to analyze")
    args = parser.parse_args()

    tube_meta = fcsparser.parse(args.fcs_file, meta_data_only = True)
    tube_meta = [(k, v) for k, v in tube_meta.items()]
    tube_meta = sorted(tube_meta)
    for k, v in tube_meta:
        print("{} : {}".format(k, v))
    
if __name__ == '__main__':
    main()
