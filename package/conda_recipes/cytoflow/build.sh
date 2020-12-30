#!/bin/bash

$PYTHON setup.py install --single-version-externally-managed --record=record.txt
$PYTHON setup.py build_sphinx -b embedded_help
$PYTHON setup.py install --single-version-externally-managed --record=record.txt

# Add more build steps here, if they are necessary.

# See
# https://conda.io/docs/user-guide/tasks/build-packages/index.html
# for a list of environment variables that are set during the build process.
