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
files using the provided FCS metadata.
"""

import argparse, warnings, pathlib, re
from copy import copy
import fcsparser
import cytoflow as flow
import cytoflow.utility as util

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fcs_file", help = "FCS file to split")
    parser.add_argument('-n', '--name_metadata', help = "FCS metadata to use as the name")
    parser.add_argument('-p', '--path', help = "Path to export files to (default: '.'", default = '.')
    parser.add_argument('-d', '--dry', action = 'store_true', help = "Dry run: say what the program would do but don't do it")
    args = parser.parse_args()
    
    # first, figure out how many data segments there are.
    for i in range(0, 99):
        with warnings.catch_warnings(record = True) as w:
            meta = fcsparser.parse(args.fcs_file, data_set = i, meta_data_only = True)
            if w and "does not contain the number of data sets" in  w[-1].message.__str__():
                return

        if args.name_metadata in meta:
            filename = meta[args.name_metadata] + '.fcs'
        else:
            filename = pathlib.Path(args.fcs_file).stem + '_{}'.format(i) + '.fcs'
            
        path = pathlib.Path(args.path) / pathlib.Path(filename)
        
        print(path)
        
        if not args.dry:
            op = flow.ImportOp(tubes = [flow.Tube(file = args.fcs_file, conditions = {})],
                               data_set = i)
            ex = op.apply()
            
            _, metadata = list(ex.metadata['fcs_metadata'].items())[0]
            metadata = copy(metadata)

            exclude_keywords = ['$BEGINSTEXT', '$ENDSTEXT', '$BEGINANALYSIS', 
                                '$ENDANALYSIS', '$BEGINDATA', '$ENDDATA',
                                '$BYTEORD', '$DATATYPE', '$MODE', '$NEXTDATA', 
                                '$TOT', '$PAR']
            metadata = {str(k) : str(v) for k, v in metadata.items()
                                        if re.search('^\$P\d+[BENRDSG]$', k) is None
                                        and k not in exclude_keywords}
        
            util.write_fcs(str(path),
                           ex.channels,
                           {c: ex.metadata[c]['range'] for c in ex.channels},
                           ex.data.values,
                           compat_chn_names = False,
                           compat_negative = False,
                           **metadata)

if __name__ == '__main__':
    main()