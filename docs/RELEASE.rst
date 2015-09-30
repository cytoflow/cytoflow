Spinning a new release
----------------------

- Update the version in ``cytoflow/__init__.py``
- Make sure ``install_requires`` in ``setup.py`` matches ``requirements.txt``
- Update the README.rst from the README.md.  From the project root, say

::

  pandoc --from=markdown --to=rst --output=README.rst README.md

- Update the API documents.  From ``docs`` say

::

  sphinx-apidoc -f -o . ../cytoflow
  
- Push the updated docs to GitHub.  Give it a few minutes, then check the
  builds on Travis_, Appveyor_ and ReadTheDocs_.
  
  .. _Travis: https://travis-ci.org/bpteague/cytoflow
  .. _Appveyor: https://ci.appveyor.com/project/bpteague/cytoflow
  .. _ReadTheDocs: https://readthedocs.org/projects/cytoflow/

- Create a new tag on the master branch matching the new version in 
  ``cytoflow/__init__.py``.  This will cause travis-ci to
  upload a new source dist to PyPI from a linux worker.
- Create the SAME TAG on the project cytoflow-wheels.  This will cause a
  travis-ci mac worker to upload a binary wheel to PyPI.
- Log on to Appveyor.  Download the two Windows wheels from the "artifacts"
  tab in the tagged build; upload to PyPI.
