Installation notes
==================

DEVELOPERS: To use the Cytoflow modules in an IPython notebook or your own code
-------------------------------------------------------------------------------

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

    conda install pip pandas numpy numexpr matplotlib scipy scikit-learn seaborn pyface envisage pyqt

* Install the package with pip::

   pip install cytoflow
   
* To verify installation, start an IPython notebook.  From the Start menu, in 
  the Anaconda folder, run ``IPython (Py 2.7) Notebook``.  In the first cell,
  type ``import cytoflow`` and press ``Shift+Enter``.  If Python doesn't complain,
  you're good to go.  (If it does, please submit a bug report!)
  

DEVELOPERS: To hack on the code
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
of Eclipse and PyDev; there's probably some Eclipse cruft (``.project`` and
``.pydevproject``) in the GitHub repo.


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

* Install the Anaconda Python distribution. **Make sure to install
  version 2.7.**  (Some day we will be Python 3 compatible, but not until 
  all of our dependencies are.)

  `Download Anaconda here <https://www.continuum.io/downloads>`_

* From the Start menu, in the Anaconda folder, run ``Anaconda Command Prompt``

* Install the conda package dependencies.  At the Anconda command prompt, type::

    conda install pip pandas numpy numexpr matplotlib scipy scikit-learn seaborn pyface envisage pyqt

* Clone the git repo.  **From git-bash**, say::

    git clone https://github.com/bpteague/cytoflow.git
    
* Now, install it in developers' mode.  From the **Anaconda prompt**, navigate
  to the directory you checked out ``cytoflow`` into and say::
  
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
  `cytoflow/operations/logicle_ext` subdirectory.
  
* **Rename the file _Logicle.pyd**

* Start an IPython notebook.  Say ``import cytoflow`` to make sure that everything
  is installed properly.  If you get an error, make sure you've followed the
  instructions above carefully then file a bug report!

USERS: Just run the code
------------------------

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
