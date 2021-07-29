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

'''
cytoflow.scripts.parse_beads
----------------------------

Parse beads.csv into a dict to go in cytoflow.operations.bead_calibration
'''


# format of the input file is CSV
# first line, first col: name
# second line, first col: URL of the source spreadsheet
# following lines: first col is calibrant, remaining cols are values
# ...until a blank line

import sys
import pandas as pd
from yapf.yapflib.yapf_api import FormatCode

def main():
    csv = pd.read_csv(sys.argv[1],  header = None)
    
    beads = {}
    curr_beads_name = ""
    curr_beads = {}
    for i, row in csv.iterrows():
        
        if str(row[0]).startswith('http'):
            continue
            
        if pd.isnull(row[1]):
            if curr_beads:
                beads[curr_beads_name] = curr_beads
                curr_beads = {}
            curr_beads_name = row[0]
            continue
            
        curr_beads[row[0]] = [v for v in row[1:] if not pd.isnull(v)]
        
    print(FormatCode(repr(beads))[0])


if __name__ == '__main__':
    main()