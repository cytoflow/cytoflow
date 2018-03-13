
"%PYTHON%" setup.py develop
"%PYTHON%" setup.py build_sphinx -b embedded_help
rd /s /q "cytoflow.egg-info"
"%PYTHON%" setup.py install
if errorlevel 1 exit 1

:: Add more build steps here, if they are necessary.

:: See
:: https://conda.io/docs/user-guide/tasks/build-packages/index.html
:: for a list of environment variables that are set during the build process.
