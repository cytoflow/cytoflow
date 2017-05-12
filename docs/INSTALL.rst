.. _install:

Installation notes
==================

To use the Cytoflow modules in an IPython notebook or your own code
-------------------------------------------------------------------

.. _ubuntu-mod:

Ubuntu
^^^^^^

On a fresh Ubuntu 14.04 install::

	# main cytoflow dependencies
	brian@vm:~$ apt-get install python-pip python-qt4 build-essential swig python-dev
	
	# we require a relatively recent version of numpy, and numpy in turn
	# requires a significant number of dependencies (cython, fortran, blas, 
	# lapack).  the easiest way to make sure you get them all is to just install
	# the build dependencies of the Ubuntu package:
	brian@vm:~$ sudo apt-get build-dep numpy 
	
	# pandas wants numpy installed separately.  i'm sure this is an upstream bug
	brian@vm:~$ pip install --upgrade --user numpy
	
	# cytoflow requires a very recent version of matplotlib.  if pip tries to 
	# install matplotlib and fails with "The following required packages can not be
	# built: freetype, png", then you have two options.  You can either install
	# just those packages...
	
	brian@vm:~$ sudo apt-get install libpng12-dev libfreetype6-dev
	
	# .... or you can install the entire set of matplotlib build dependencies
	# (gets you LaTeX support, among other niceties, but the packages sum to
	# 500 Mb!)
	
	brian@vm:~$ sudo apt-get build-dep matplotlib
	
	# install matplotlib
	brian@vm:~$ pip install --upgrade --user matplotlib
	
	# finally, install cytoflow:
	brian@vm:~$ pip install --upgrade --user cytoflow
	
	# if you want to use the IPython/Jupyter notebook (and you should!), do
	brian@vm:~$ pip install --upgrade jupyter
	
.. _windows-mod:
	
Windows
^^^^^^^

**This is not the only way to get CytoFlow up and running, but it is by far
the fastest.**

* Start by installing the Anaconda Python distribution. **Make sure to install
  version 2.7.**  (Some day we will be Python 3 compatible, but not until 
  all of our dependencies are.)

  `Download Anaconda here <https://www.continuum.io/downloads>`_

* From the Start menu, in the Anaconda folder, run ``Anaconda Command Prompt``

* Install the conda package dependencies.  At the command prompt, type::

    conda install pandas bottleneck numpy numexpr matplotlib scipy scikit-learn seaborn traits pyface envisage nbformat python-dateutil statsmodels qt pip

* Install the package with pip::

   pip install cytoflow
   
* To verify installation, start an IPython notebook.  From the Start menu, in 
  the Anaconda folder, run ``IPython (Py 2.7) Notebook``.  In the first cell,
  type ``import cytoflow`` and press ``Shift+Enter``.  If Python doesn't complain,
  you're good to go.  (If it does, please submit a bug report!)
  
MacOS
^^^^^

** As with Windows, this is not the only way to install CytoFlow but it is the fastest.

* Start by installing the Anaconda Python distribution. **Make sure to install
  version 2.7.**  (Some day we will be Python 3 compatible, but not until 
  all of our dependencies are.)

  `Download Anaconda here <https://www.continuum.io/downloads>`_
 
* Start the Terminal.
 
* Install the conda package dependencies.  At the Terminal prompt, type::
     
     conda install pandas bottleneck numpy numexpr matplotlib scipy scikit-learn seaborn traits pyface envisage nbformat python-dateutil statsmodels qt pip
     
* Install the `cytoflow` package with `pip`.  At the Terminal prompt, type::
     
     pip install cytoflow
     
* To verify the installation, start a Jupyter notebook from the Anaconda Navigator.  A
  browser window will open.  Create a new Python 2 notebook, and in the first cell type
  ``import cytoflow`` and press ``Shift+Enter``.  If Python doesn't complain,
  you're good to go.  (If it does, please submit a bug report!)

.. _hacking:

To hack on the code
-------------------------------

Ubuntu
^^^^^^

On a fresh Ubuntu 14.04 install::

	# much of this looks like above.

	# main cytoflow dependencies
	brian@vm:~$ apt-get install python-pip python-qt4 swig python-dev
	
	# we require a relatively recent version of numpy, and numpy in turn
	# requires a significant number of dependencies (cython, fortran, blas, 
	# lapack).  the easiest way to make sure you get them all is to just install
	# the build dependencies of the Ubuntu package:
	brian@vm:~$ sudo apt-get build-dep numpy 
	
	# pandas wants numpy installed separately.  i'm sure this is an upstream bug
	brian@vm:~$ pip install --upgrade --user numpy
	
	# cytoflow requires a very recent version of matplotlib.  if pip tries to 
	# install matplotlib and fails with "The following required packages can not be
	# built: freetype, png", then you have two options.  You can either install
	# just those packages...
	
	brian@vm:~$ sudo apt-get install libpng12-dev libfreetype6-dev
	
	# .... or you can install the entire set of matplotlib build dependencies
	# (gets you LaTeX support, among other niceties, but the packages sum to
	# 500 Mb!)
	
	brian@vm:~$ sudo apt-get build-dep matplotlib
	
	# install matplotlib
	brian@vm:~$ pip install --upgrade --user matplotlib
	
	# here's where things diverge.  clone the repo from github
	brian@vm:~$ sudo apt-get install git
	brian@vm:~$ git clone https://github.com/bpteague/cytoflow.git
	
	# and install the requirements from requirements.txt, but don't install
	# the cytoflow package itself!
	brian@vm:~$ cd cytoflow
	brian@vm:~/cytoflow$ pip install --user -r requirements.txt
	
	# now, install cytoflow in developer mode so you can hack on it in the
	# source directory and run it from python to test
	brian@vm:~/cytoflow$ python setup.py develop --user
	
Now you can use whatever development environment floats your boat.  I'm a fan
of Eclipse and PyDev.


Windows
^^^^^^^

``cytoflow`` has one C++ module, compiled with ``swig``.  Unfortunately, compiling
modules on Windows requires Microsoft Visual C++, which is a huge dependency
and a huge pain in the ass.  And once you get it installed, setting up 
Python to talk with it?  Forget about it.

The instructions below assume that you do not want to fight that fight. Instead,
the ``cytoflow`` continuous integration servers build the compiled extension, and
when I roll a release they get posted on the GitHub release page.

* Install a copy of ``git``.  I use `git-for-windows <http://git-for-windows.github.io>`_

* Clone the git repo.  **From git-bash**, say::

    git clone https://github.com/bpteague/cytoflow.git

* Install the Anaconda Python distribution. **Make sure to install
  version 2.7.**  (Some day we will be Python 3 compatible, but not until 
  all of our dependencies are.)

  `Download Anaconda here <https://www.continuum.io/downloads>`_

* From the Start menu, in the Anaconda folder, run ``Anaconda Command Prompt``

* Install the conda package dependencies.  From the cytoflow source directory, say::

    conda install --file=packaging/conda-requirements.txt
    conda install pip
    
* Now, install it in developers' mode.  From the cytoflow source dirctory, say::
  
    pip install --user -r requirements.txt
    set NO_LOGICLE=True
    python setup.py develop
    
  This should complete successfully.  If it dies with 
  ``command 'swig.exe' failed``, make sure you set NO_LOGICLE, try it again,
  then please file a bug report.
  
* Download the appropriate extension from the `cytoflow releases page
  <https://github.com/bpteague/cytoflow/releases>`_ -- either
  ``_Logicle-amd64.pyd`` if you're running a 64-bit version of Windows,
  or ``_Logicle-win32.pyd`` if you're running a 32-bit version of Windows.
  
* Copy the file into your source directory; put it in the 
  `cytoflow/utility/logicle_ext` subdirectory.
  
* **Rename the file _Logicle.pyd**

* Start an IPython notebook.  Say ``import cytoflow`` to make sure that everything
  is installed properly.  If you get an error, make sure you've followed the
  instructions above carefully then file a bug report!

  
MacOS
^^^^^

``cytoflow`` has one C++ module, compiled with ``swig``.  On MacOS, you have two options
to get this file:  you can download `XCode <http://developer.apple.com/xcode/download>`_, 
with which you should be able to build the C++ extension using the usual ``python setup.py build``.

The other alternative is to suck the compiled extension out of one of the
pre-built MacOS Python packages.  That's the approach outlined below.

* Install a copy of ``git`` from `the Git website <http://www.git-scm.com>`_.

* Clone the git repo.  In your working folder, say::

    git clone https://github.com/bpteague/cytoflow.git

* Install the Anaconda Python distribution. **Make sure to install
  version 2.7.**  (Some day we will be Python 3 compatible, but not until 
  all of our dependencies are.)

  `Download Anaconda here <https://www.continuum.io/downloads>`_

* Install the conda package dependencies.  In a Mac Terminal, type::

    conda install --file=packaging/conda-requirements.txt
    conda install pip
    
* Now, install it in developers' mode::
    
    pip install --user -r requirements.txt
    NO_LOGICLE=True python setup.py develop
    
  This should complete successfully.  If it dies with 
  ``SystemError: Cannot locate working compiler``, make sure you set NO_LOGICLE, try it again,
  then please file a bug report.
  
* Download the ``cytoflow`` wheel from the Github release page or the PyPI release.  These 
  commands get version 0.4.1 from PyPI; but the Logicle extension hasn't changed in many 
  releases, and hopefully won't be changing any time soon, so they are likely still valid
  for the master Git branch::
  
    mkdir build
    cd build
    curl https://pypi.python.org/packages/86/dc/287ba2a15660511b3c3cd0f4b77692b073eabcc9c58bb55824c00c59d0ea/cytoflow-0.4.1-cp27-cp27m-macosx_10_6_x86_64.whl -o cytoflow.zip
    unzip cytoflow.zip
    cp cytoflow/utility/logicle_ext/_Logicle.so ../cytoflow/utility/logicle_ext/

* Start an IPython notebook.  Say ``import cytoflow`` to make sure that everything
  is installed properly.  If you get an error, make sure you've followed the
  instructions above carefully then file a bug report!
  

Running the point-and-click GUI program
-----------------------------------------------

**If you just want to run a pre-built program, there are one-click bundles 
available at** 
`http://bpteague.github.io/cytoflow <http://bpteague.github.io/cytoflow>`_.

Ubuntu
^^^^^^

What, you were expecting a ``.deb`` package?

* To install, follow the :ref:`instructions for installing the 
  modules<ubuntu-mod>`. 
  
* Set the ``QT_API`` environment variable.  From a shell, say::

    export QT_API=pyqt

* As long as the path that ``pip`` installs to is in your ``PATH`` variable,
  you should just be able to run ``cytoflow`` from the same shell.  If not,
  try::
  
    ~/.local/bin/cytoflow


Windows
^^^^^^^

* Start by following all the :ref:`instructions above for installing the 
  modules<windows-mod>`.

* Set the QT_API environment variable globally.  In the Anaconda command
  prompt, type::
  
    setx QT_API "pyqt"
    
* Use the Windows Search tool to find ``cytoflow.exe``.  Hold down ``Alt``
  and drag a shortcut to the desktop.  Double-click to run ``cytoflow``
