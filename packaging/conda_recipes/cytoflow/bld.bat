:: "%PYTHON%" setup.py build_sphinx
"%PYTHON%" setup.py install

if errorlevel 1 exit 1

:: Add more build steps here, if they are necessary.

:: See
:: https://conda.io/docs/user-guide/tasks/build-packages/index.html
:: for a list of environment variables that are set during the build process.
