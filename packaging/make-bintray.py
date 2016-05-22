#!/usr/bin/env python

from __future__ import print_function

json_dev = """
{{
    "package": {{
        "name": "cytoflow-dev",
        "repo": "cytoflow",
        "subject": "bpteague"
    }},

    "version": {{
        "name": "{0}",
        "desc": "Binaries for git commit {0}",
        "released": "{1}"
    }},
   
    "files":
        [
            {{"includePattern": "dist/(.*)", 
             "matrixParams": {{"override": 1 }} }}
        ]
}}
"""

json_release = """
{{
    "package": {{
        "name": "cytoflow-release",
        "repo": "cytoflow",
        "subject": "bpteague"
    }},

    "version": {{
        "name": "{0}",
        "desc": "Binaries for git tag {0}",
        "released": "{1}",
        "vcs_tag" : "{0}",
    }},
   
    "files":
        [
            {{"includePattern": "dist/(.*)", 
             "matrixParams": {{"override": 1 }} }}
        ],

   "publish": true 
}}
"""

import subprocess
git_tag = subprocess.check_output(['git', 'describe', '--tags'])
git_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'])[0:7]

from datetime import date
d = date.today().isoformat()

if git_tag.find('-') == -1:
    print(json_release.format(git_tag, d))
else:
    print(json_dev.format(git_hash, d))

