======================
Spinning a new release
======================

Tests
-----

- We use three continuous integration platforms:
  `Travis <https://travis-ci.org/bpteague/cytoflow>`_, 
  `Appveyor <https://ci.appveyor.com/project/bpteague/cytoflow>`_, and
  `ReadTheDocs <https://readthedocs.org/projects/cytoflow/>`_.
  We also publish to `Anaconda Cloud <https://anaconda.org/>`_.
  Temporary build artifacts get published to `Bintray <https://bintray.com/bpteague/cytoflow/cytoflow#files>`_.

- Make sure that the :mod:`cytoflow` tests pass, both locally and on Travis and Appveyor::

  	  nose2 -c package/nose2.cfg -s cytoflow/tests
  
- Make sure the :mod:`cytoflowgui` tests pass.  
  **You must do this locally; it runs too long for the free CI platforms.** ::

  	  nose2 -c package/nose2.cfg -s cytoflowgui/tests

- Make sure that the ReadTheDocs build is working.
  
- Make sure that the :mod:`pyinstaller` distribution will build on your local 
  machine.  ::

  	  pyinstaller package/pyinstaller.spec

- Make sure that the expected files (installers, conda packages, wheels, built extensions)
  are getting published to Bintray.  Remember -- a failed deployment doesn't show
  up on the CI platforms as a broken build!
  
- Make sure that :mod:`pyinstaller` built the executables on all three supported
  platforms.  Download and test that all three start and can run a basic workflow.

    
Documentation
-------------

- Build the API docs and check them for completeness::

      python3 setup.py build_sphinx
  
- Build the online docs and check them for completeness::

  	  python3 setup.py build_sphinx -b embedded_help

Versioning and dependencies
---------------------------

- We're using ``versioneer`` to manage versions.  No manual versions required.

- If there are dependencies that don't have packages on Anaconda, add recipes
  to ``package/conda_recipes`` (using ``conda skeleton``) and upload them to
  the Anaconda Cloud.  Unless there's a really (really!) good reason, please
  make them no-arch.
  
- Make sure ``install_requires`` in ``setup.py`` matches ``requirements.txt``

- Update the README.rst from the README.md.  From the project root, say::

  	pandoc --from=markdown --to=rst --output=README.rst README.md
  
- Push the updated docs to GitHub.  Give the CI builders ~30 minutes, then 
  check the build status on Travis_, Appveyor_, ReadTheDocs_ and `Anaconda Cloud`_.

- Create a new tag on the master branch.  This will re-build everything on the CI
  builders, create a new release on GitHub, and upload new source and wheels to 
  PyPI and packages to Anaconda Cloud.
 
- Double-check that the required files ended up on Bintray_.

- On branch ``gh-pages``, update the version in ``_config.yml``.  Push these
  changes to update the main download links on 
  http://bpteague.github.io/cytoflow

- Download the wheels from Bintray or Github and add them to PyPI.  
  TODO - use ``twine`` to release to PyPI from CI builders.
