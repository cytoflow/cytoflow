#!/bin/bash

if [[ $TRAVIS_OS_NAME == 'osx' ]]; then
    brew update
    brew install swig

    wget http://repo.continuum.io/miniconda/Miniconda-3.5.2-MacOSX-x86_64.sh -O miniconda.sh
    chmod +x miniconda.sh
    ./miniconda.sh -b
    export PATH=/Users/travis/miniconda/bin:$PATH
    conda update --yes conda

else
    # Linux x86_64
    wget http://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh -O miniconda.sh
    chmod +x miniconda.sh
    ./miniconda.sh -b
    export PATH=/home/travis/miniconda2/bin:$PATH
    conda update --yes conda    

fi
