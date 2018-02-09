======================
Spinning a new release
======================

Tests
-----

- We use three continuous integration platforms:
  `Travis <https://travis-ci.org/bpteague/cytoflow>`, 
  `Appveyor <https://ci.appveyor.com/project/bpteague/cytoflow>`, and
  `ReadTheDocs <https://readthedocs.org/projects/cytoflow/>`.

- Make sure that the ``cytoflow`` tests pass, both locally and on Travis and Appveyor::

  nose2 -c packaging/nose2.cfg -s cytoflow/tests
  
- Make sure the ``cytoflowgui`` tests pass.  
**You must do this locally; it runs too long for the free CI platforms.**::

  nose2 -c packaging/nose2.cfg -s cytoflowgui/tests

- Make sure that the ReadTheDocs build is working.
  
- Make sure that ``pyinstaller`` will build on your local machine.  We are 
  currently building with PyInstaller v3.1.1::

  pyinstaller packaging/pyinstaller.spec
  
- Make sure that ``pyinstaller`` built the executables on all three supported
platforms.  Download and test that all three start and can run a basic workflow.
  
Documentation
-------------

- Build the API docs and check them for completeness::

  python3 setup.py build_sphinx
  
- Build the online docs and check them for completeness::

  python3 setup.py build_sphinx -b embedded_help

Versioning and dependencies
---------------------------

- Update the version in ``cytoflow/__init__.py``
- Make sure ``install_requires`` in ``setup.py`` matches ``requirements.txt``
- Make sure the ``install_requires`` in ``setup.py`` matches ``packaging/conda-requirements.txt``
- Make sure the ``conda --install`` commands in ``INSTALL.rst`` match ``packaging/conda_requirements.txt``
- Update the README.rst from the README.md.  From the project root, say::

  pandoc --from=markdown --to=rst --output=README.rst README.md
  
- Push the updated docs to GitHub.  Give the CI builders ~30 minutes, then 
  check the build status on Travis_, Appveyor_ and ReadTheDocs_.

- Create a new tag on the master branch matching the new version in 
  ``cytoflow/__init__.py``.  This will re-build everything on the CI
  builders, create a new release on GitHub, and upload new source and
  MacOS wheels to PyPI.

- On branch ``gh-pages``, update the version in ``_config.yml``.  Push these
  changes to update the main download links on 
  http://bpteague.github.io/cytoflow

- Add the Windows wheels and installers to PyPI.  TODO - make AppVeyor use
  ``twine`` to release to PyPI too.
