.. _install:

Installation notes
==================

To use the Cytoflow modules in a Jupyter notebook or your own code
-------------------------------------------------------------------

.. _modules:

Cytoflow is available as a package for the Anaconda scientific Python
distribution.  You can install *cytoflow* through the Anaconda Navigator,
or by using the command line.

**This is not the only way to get Cytoflow up and running, but it is by far
the most straightforward.**

Installing from the ``Anaconda Navigator``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Start by installing the Anaconda Python distribution. **Make sure to install
  a 64-bit version, unless you will be building *cytoflow* yourself and you know
  what you're doing.** 

  `Download Anaconda here <https://www.anaconda.com/products/individual>`_

* Either from the Start Menu (Windows) or the Finder (Mac), run the 
  ``Anaconda Navigator``
  
* Click the ``Channels`` button.
  
  .. image:: images/channels.PNG
  
* Click ``Add...`` and type ``cytoflow``.  Select "Update channels."
  
  .. image:: images/add-channels.PNG
  
* The application ``cytoflow`` should appear in the launcher.  
  Click the ``Install`` button. 
  
  .. image:: images/new-app.PNG
  
* ``Navigator`` asks if you'd like to install in a new environment.  
  Say ``Yes``..
  
  .. image:: images/new-env.PNG
  
  **NOTE: Be patient. Anaconda Navigator is slow.**
  **NOTE: Make sure that you choose an environment that does not already exist!**

* To verify installation, start a Jupyter notebook.

  * First, *make sure you have the ``cytoflow`` environment selected.*
  * From the ``Anaconda Navigator``, install and then launch ``Jupyter notebook``.
  * Create a new *Python 3* notebook.
  * In the first cell, type ``import cytoflow`` and press ``Shift+Enter``.  
    If Python doesn't complain, you're good to go.  (If it does, please submit 
    a bug report at https://github.com/cytoflow/cytoflow/issues )
  
* **Note: When you install Cytoflow this way, the point-and-click 
  application is installed as well.**  Launching it from the 
  ``Anaconda Navigator`` will be significantly faster than downloading the
  pre-packaged binary.

Installing from the command line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Start ``Anaconda Prompt`` from the Start Menu (Windows) or Finder (Mac).

* Add the ``cytoflow`` channel::

    conda config --add channels cytoflow

* Create a new environment and install ``cytoflow`` and the Jupyter notebook.  
  In this example, the new environment will be called ``cf`` -- feel free to
  choose a different name::
  
    conda create --name cf cytoflow notebook
    
* Activate the new environment::

    conda activate cf
    
* Launch the Jupyter notebook::

    jupyter notebook
    
* Create a new *Python 3* notebook.  In the first cell, type ``import cytoflow``
  and press ``Shift+Enter``.  If Python doesn't complain, you're good to go.  
  (If it does, please submit a bug report!)
  
* This method ALSO installs the GUI. You should be able to run it by activating
  your new environment and running the ``cytoflow`` script.
  

.. _hacking:

To hack on the code
-------------------

Cytoflow depends on a huge number of libraries from the Scientific Python 
ecosystem, and a change in any one of their APIs will break the ``cytoflow``
library.  So, I have pinned the versions of all of ``cytoflow``'s dependencies,
which all but guarantees that you'll need to install into a virtual environment.
This will ensure that the rest of your Python installation doesn't break.

I strongly recommend using Anaconda to install the proper dependencies.  
A PyPI package (installable using ``pip``) is also available.  The following
instructions assume that you have installed Anaconda (as above) and launched
an Anaconda prompt.

Finally, ``cytoflow`` relies on one C++ extension.  On Linux, installing the
requirements for building it is straightforward.  On MacOS it is harder, and
on Windows it is extremely difficult.  Instead, as part of rolling a new
release, the appropriate files are made available on 
`the GitHub releases page <https://github.com/cytoflow/cytoflow/releases>`_.  
The procedure below includes instructions for downloading and installing
the appropriate file.

* Install the development dependencies

  * On Ubuntu: ``apt-get git swig python-dev``
  * On Windows: Install a copy of ``git``.  I use `git-for-windows <http://git-for-windows.github.io>`_
  * On MacOS: Install a copy of ``git`` from `the Git website <http://www.git-scm.com>`_.

* If you haven't, add the ``cytoflow`` channel to conda::

    conda config --add channels cytoflow

* Clone the repository::

    git clone https://github.com/cytoflow/cytoflow.git

* Create a new environment.  In this example, I have called it ``cf_dev``.
  In the new repository you just cloned, say::

    conda env create --name cf_dev --file environment.yml
  
* Activate the new environment::
    
    conda activate cf_dev

  
* **On Windows and MacOS only,** do the following to prevent ``cytoflow``
  from trying to build the C++ extension.
  
  * **On Windows (in CMD)**::
  
       set NO_LOGICLE=True
 
  * **On MacOS (or on Windows bash)**::
  
       export NO_LOGICLE=True
    
* Install ``cytoflow`` in developer's mode::

    python setup.py develop
    
* From the `GitHub releases page <https://github.com/cytoflow/cytoflow/releases>`_ 
  download the appropriate extension file for the version you're installing.
  
  * **On Windows (64-bit)**: ``_Logicle.cp38-win_amd64.pyd``
  * **On MacOS**: ``_Logicle.cpython-38m-darwin.so``
  
* Copy the file you just download into the `cytoflow/utility/logicle_ext/` folder
  in your source tree.
  
* Test that everything works.  Start a ``python`` interpreter and say::

    import cytoflow
    
  If you don't get any errors, you're good to go.
   

Running the point-and-click GUI program
---------------------------------------

There are one-click bundles available at http://cytoflow.github.io/

Alternately, you can follow the instructions above for installing the 
Anaconda package, then run ``cytoflow`` through the Anaconda Navigator or
via the command line.

