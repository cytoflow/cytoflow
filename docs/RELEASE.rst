Spinning a new release
----------------------

- Update the version in ``cytoflow/__init__.py``
- Update the version in ``docs/conf.py``
- Make sure ``install_requires`` in ``setup.py`` matches ``requirements.txt``
- Make sure the ``install_requires`` in ``setup.py`` matches ``packaging/conda-requirements.txt``
- Make sure the ``conda --install`` commands in ``INSTALL.rst`` match ``packaging/conda_requirements.txt``
- Update the README.rst from the README.md.  From the project root, say

::

  pandoc --from=markdown --to=rst --output=README.rst README.md

- Update the API documents.  From ``docs`` say

::

  sphinx-apidoc -f -o . ../cytoflow
  
- Push the updated docs to GitHub.  Give the CI builders ~30 minutes, then 
  check the build status on Travis_, Appveyor_ and ReadTheDocs_.
  
  .. _Travis: https://travis-ci.org/bpteague/cytoflow
  .. _Appveyor: https://ci.appveyor.com/project/bpteague/cytoflow
  .. _ReadTheDocs: https://readthedocs.org/projects/cytoflow/

- Optionally, perform functional testing on the latest platform binaries
  at Bintray_

  .. _Bintray: https://bintray.com/bpteague/cytoflow/cytoflow#files

- Create a new tag on the master branch matching the new version in 
  ``cytoflow/__init__.py``.  This will re-build everything on the CI
  builders, create a new release on GitHub, and upload new source and
  MacOS wheels to PyPI.

- On branch ``gh-pages``, update the version in ``_config.yml``.  Push these
  changes to update the main download links on 
  http://bpteague.github.io/cytoflow

- Add the Windows wheels and installers to PyPI.  TODO - make AppVeyor use
  ``twine`` to release to PyPI too.
