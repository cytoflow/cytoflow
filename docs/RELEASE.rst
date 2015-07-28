When spinning a new release:
 - Create a new tag on the master branch.  This will cause travis-ci to
   upload a new source dist to PyPI from a linux worker.
 - Create the SAME TAG on the project cytoflow-wheels.  This will cause a
   travis-ci mac worker to upload a binary wheel to PyPI.
 - Log on to Appveyor.  Download the two Windows wheels from the "artifacts"
   tab in the tagged build; upload to PyPI.