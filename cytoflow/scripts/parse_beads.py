# format of the input file is CSV
# first line, first col: name
# second line, first col: URL of the source spreadsheet
# following lines: first col is calibrant, remaining cols are values
# ...until a blank line

import sys
import pandas as pd
from yapf.yapflib.yapf_api import FormatCode

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

