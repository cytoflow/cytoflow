=======================================================
Welcome to Cytoflow's user and developer documentation!
=======================================================

*********************************************************
I want to see the point-and-click program's documentation
*********************************************************

Here's the :ref:`manual <manual>`.  At the moment it's pretty sparse,
but there's a :ref:`tutorial <01_quickstart>` that should help you get started.
Also, check out the online help in the "Help" pane.

*************************************************************
I want to use Cytoflow's modules in my own cytometry analysis
*************************************************************

Great!  May I recommend you start with some example Jupyter notebooks.
They provide a good introduction to both basic modules and some of
Cytoflow's more advanced features.

* `Basic flow cytometry analysis <https://github.com/bpteague/cytoflow/blob/master/docs/examples-basic/Basic%20Cytometry.ipynb>`_
* `An small-molecule induction curve with yeast <https://github.com/bpteague/cytoflow/blob/master/docs/examples-basic/Yeast%20Dose%20Response.ipynb>`_
* `Machine learning methods applied to flow cytometry <https://github.com/bpteague/cytoflow/blob/master/docs/examples-basic/Machine%20Learning.ipynb>`_
* `Reproduced an analysis from a published paper <https://github.com/bpteague/cytoflow-examples/blob/master/kiani/Kiani%20Nature%20Methods%202014.ipynb>`_
* `A multidimensional induction in yeast <https://github.com/bpteague/cytoflow-examples/blob/master/yeast/Induction%20Timecourse.ipynb>`_
* `Calibrated flow cytometry in MEFLs <https://github.com/bpteague/cytoflow-examples/blob/master/tasbe/TASBE%20Workflow.ipynb>`_

If you decide you want to have a go, see the :ref:`installation notes <install>`.
Quick hint: if you have Anaconda installed, say::

  conda config --add channels bpteague
  conda create --name cytoflow cytoflow 
  
This creates a new Anaconda environment named ``cytoflow`` and installs the 
latest package from the Anaconda Cloud.

For more details of these modules, you're likely to want to see the 
:ref:`module documents <modindex>`

********************************
I want to help develop Cytoflow.
********************************

Hooray!  Have a look at the :ref:`install documentation <hacking>` for how to
get the source code installed.  Then, have a look at the  
:ref:`design docs <design>` and the :ref:`new modules <new_modules>` documentation.
Finally, join us over at 
`the cytoflow GitHub repo <https://github.com/bpteague/cytoflow>`_ to file bugs, submit PRs, etc.

*********
Contents:
*********

.. toctree::
   :maxdepth: 1

   manual
   
   INSTALL
   design
   new_modules
   RELEASE
   cytoflow
   
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

