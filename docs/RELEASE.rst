======================
Spinning a new release
======================

Tests
-----

- We use two continuous integration platforms to run tests and build binaries and documentations:
  `GitHub Actions <https://github.com/cytoflow/cytoflow/actions>`_, 
  `ReadTheDocs <https://readthedocs.org/projects/cytoflow/>`_.
  
  Finished releases are published to `GitHub releases <https://github.com/cytoflow/cytoflow/releases>`_,
  `Anaconda Cloud <https://anaconda.org/cytoflow>`_, and the `Python Package Index <https://pypi.org/project/cytoflow/>`_.
  
- Make sure that the :mod:`cytoflow` tests pass, both locally and on GitHub::

  	  nose2 -c package/nose2.cfg -s cytoflow/tests -N 8
  
- Make sure the :mod:`cytoflowgui` tests pass.  
  **You must do this locally; I'm still working on why it doesn't run on the CI platform.** ::

  	  nose2 -c package/nose2.cfg -s cytoflowgui/tests -N 8
  	  
    
Documentation
-------------

- Build the API docs and check them for completeness::

      python setup.py build_sphinx
  
- Build the online docs and check them for completeness::

  	  python setup.py build_sphinx -b embedded_help
  	  
Packaging
---------
  	  
- Build the conda package locally::

      conda build package/conda_recipes/cytoflow
      
- Install the local package in a new environment::

      conda create --name cytoflow.test --use-local cytoflow
      
- Activate the test environment, make sure you can import cytoflow, and make sure the GUI runs::

      conda activate cytoflow.test
      python -c "import cytoflow"
      cytoflow    

- Make sure that the :mod:`pyinstaller` distribution will build on your local 
  machine (back in your development environment).  ::

  	  pyinstaller package/pyinstaller.spec 

- Make sure that the ReadTheDocs build is working.
  
- Make sure that :mod:`pyinstaller` built the executables on all three supported
  platforms.  Download and test that all three start and can run a basic workflow.



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
  	
Tag and upload the release
--------------------------
  
- Push the updated docs to GitHub.  Give the CI builders ~30 minutes, then 
  check the build status on GitHub, and ReadTheDocs.

- Create a new tag on the master branch.  This will re-build everything on the CI
  builders.

- Download the artifacts.

Sign the Windows installer
--------------------------
To get rid of the "Unknown developer" warning in Windows, we sign the installer.
This requires a hardware crypto token, so it must be done locally.

- Setup: If not done already, download and install the Windows Platform SDK. I'm using 8.1 
  because I couldn't get 10 to install.

- Download the Windows installer from Github.

- Open a terminal in C:\Program Files\Microsoft Platform SDK\Bin.

- Start the signing wizard::

    signtool.exe signwizard
    
- Select the installer binary.  

- Under "Signing options", choose "Typical"

- Under "Signature Certificate", choose "Select from store...".  If the hardware key is installed 
  and set up properly, Windows should find the correct certificate.
  
- Add a description such as "Flow cytometry software".  For "Web location", specify "http://cytoflow.readthedocs.org"

- Check the box next to "Add a timestamp to data".  Enter "http://time.certum.pl".  (Probably could use digicert or some other service.)

- When prompted, enter the Common Profile PIN.

- After the wizard closes, double-check that the signing process was completed by right-clicking on the executable and checking the "Digital Signatures" tab.

Upload the artifacts and update the homepage
--------------------------------------------

- Upload artifacts as appropriate to GitHub, Anaconda, and the Python Package Index.  
  (Make sure that in the case of Anaconda, you're uploading to the organization account, not
  your personal account!)

- At https://github.com/cytoflow/cytoflow.github.io, update the version in 
  ``_config.yml``. Push these changes to update the main download links on 
  http://cytoflow.github.io/
  
- Verify that the download links at http://cytoflow.github.io/ still work!

