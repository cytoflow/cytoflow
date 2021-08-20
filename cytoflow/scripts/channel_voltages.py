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
cytoflow.scripts.channel_voltages
---------------------------------

Returns the channel voltages ($PnV) for the given FCS file.
"""

import argparse

import cytoflow as flow

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fcs_file", help = "FCS file to analyze")
    args = parser.parse_args()

    op = flow.ImportOp(tubes = [flow.Tube(file = args.fcs_file, conditions = {})])
    ex = op.apply()
    for c in ex.channels:
        m = ex.metadata[c]
        if "voltage" in m:
            print("{0}\t{1}".format(c, m["voltage"]))
    
if __name__ == '__main__':
    main()
