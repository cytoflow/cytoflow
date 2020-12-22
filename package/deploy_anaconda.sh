#!/bin/bash

# this script uses the ANACONDA_TOKEN env var. 
# to create a token:
# >>> anaconda login
# >>> anaconda auth -c -n travis --max-age 307584000 --url https://anaconda.org/USERNAME/PACKAGENAME --scopes "api:write api:read"
set -e
set -x

echo "Deploying to Anaconda.org..."
anaconda -t $ANACONDA_TOKEN upload $HOME/miniconda3/conda-bld/**/cytoflow-*.tar.bz2

echo "Successfully deployed to Anaconda.org."
exit 0
