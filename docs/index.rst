Cytoflow: Better quantitative flow cytometry.
=============================================

Cytoflow is a **point-and click program** and a **Python library** for
analyzing flow cytometry data.  It was written by Brian Teague to address
shortcomings in currently-available flow software.

How is Cytoflow different?
--------------------------

* An emphasis on **metadata.**  Cytoflow assumes you are measuring the
  fluorescence of several samples that were treated differently:
  collected at different times, treated with varying levels of a chemical,
  etc.  You specify these sample conditions up front, then use those 
  conditions to control your analysis.
* The analysis is represented as a **workflow**.  Operations such as gating
  and compensation are applied sequentially; a workflow can be saved a re-used
  or shared with colleagues.
* **Good visualization.** Make publication-ready plots right from the software.
* **Thoughtful documentation.**  Each module, operation and visualization is
  documented, and particular attention has been paid to getting users 
  up-and-running quickly.
* Cytoflow is built on **Python modules** that you can use in your own 
  workflows.  The library was designed to work particularly well in a 
  `Jupyter notebook <https://jupyter.org/>`_.  
* Cytoflow is **free and open-source.**  Contribute bug reports at the 
  `GitHub project page <https://github.com/bpteague/cytoflow>`_
  or download the source code to modify it for your own needs.  Then,
  contribute your changes back so the rest of the community can benefit from
  them.
  
If you'd like to see Cytoflow in action, here are some 
:ref:`screenshots <screenshots>`, or you can check out a 
`screencast on Youtube <https://www.youtube.com/watch?v=vfEfeFGVtro>`_.
  
Getting Started
---------------

Quick installation instructions:

* **Windows**: `Download the installer <https://github.com/bpteague/cytoflow/releases/download/1.0/cytoflow-installer-1.0-win-amd64.exe>`_, 
  then run it.
* **MacOS (10.10+)**: `Download the ZIP file <https://github.com/bpteague/cytoflow/releases/download/1.0/cytoflow-1.0.macos.zip>`_.  
  Unzip the file, then double-click to run the program.  Depending on your
  security settings, you may have to specifically enable this program 
  (it's not signed.)
* **Linux**: `Download the tarball <https://github.com/bpteague/cytoflow/releases/download/1.0/cytoflow-1.0.linux_x86-64.tar.gz>`_.
  Extract it, then run the *cytoflow* binary.
  
More detailed installation instructions :ref:`can be found in the user's manual. <user_manual>`.

Documentation
-------------

The :ref:`user manual <user_manual>` is broken into four different sets of
documentation:

* :ref:`Tutorials <user_tutorials>` take you step-by-step through some basic
  analyses.  Start here if you're new to Cytoflow.
* :ref:`How-to guides <user_howto>` are recipes. They guide you through some
  common use-cases.  They are more advanced than tutorials and assume some 
  knowledge of how Cytoflow works.
* :ref:`User guides <user_guides>` discuss how Cytoflow works "under the hood",
  which can make you a better Cytoflow user for more advanced or non-standard
  analyses.
* :ref:`Reference pages <user_reference>` document every operation and view.
  These are the same pages that are displayed in Cytoflow's "Help" panel.


<<<<<<< Upstream, based on master
<<<<<<< Upstream, based on master
* `Basic flow cytometry analysis <https://github.com/cytoflow/cytoflow/blob/master/docs/examples-basic/Basic%20Cytometry.ipynb>`_
* `An small-molecule induction curve with yeast <https://github.com/cytoflow/cytoflow/blob/master/docs/examples-basic/Yeast%20Dose%20Response.ipynb>`_
* `Machine learning methods applied to flow cytometry <https://github.com/cytoflow/cytoflow/blob/master/docs/examples-basic/Machine%20Learning.ipynb>`_
* `Reproduced an analysis from a published paper <https://github.com/cytoflow/cytoflow-examples/blob/master/kiani/Kiani%20Nature%20Methods%202014.ipynb>`_
* `A multidimensional induction in yeast <https://github.com/cytoflow/cytoflow-examples/blob/master/yeast/Induction%20Timecourse.ipynb>`_
* `Calibrated flow cytometry in MEFLs <https://github.com/cytoflow/cytoflow-examples/blob/master/tasbe/TASBE%20Workflow.ipynb>`_
=======
**********************************************************
I want to see the point-and-click program's documentation.
**********************************************************
>>>>>>> 9522eaf docs: refactor documentation (in progress)
=======
For Developers
--------------
>>>>>>> e2b029c Docs: structure for users' and developers' manuals.

If you want to use `Python <https://www.python.org/>`_ to analyze flow
cytometry data, then Cytoflow is for you!  I've found Cytoflow useful
for both *interactive data exploration* (ie, poking data to see what it's
telling you) and *automated data analysis* (ie, writing scripts and pipelines
to process lots of data.)  

<<<<<<< Upstream, based on master
<<<<<<< Upstream, based on master
  conda config --add channels cytoflow
  conda create --name cytoflow cytoflow 
  
This creates a new Anaconda environment named ``cytoflow`` and installs the 
latest package from the Anaconda Cloud.
=======
*****************************************************************
I want to write my own cytometry analysis pipeline in Python 3.x.
*****************************************************************
>>>>>>> 9522eaf docs: refactor documentation (in progress)
=======
To get a taste of what Cytoflow can do, check out an 
`example Jupyter notebook <https://github.com/bpteague/cytoflow/blob/master/docs/examples-basic/Basic%20Cytometry.ipynb>`_.
>>>>>>> e2b029c Docs: structure for users' and developers' manuals.

Then, head over to the :ref:`developers' manual <dev_manual>`.  There,
you'll find:

* :ref:`Tutorial Jupyter notebooks <dev_tutorials>` to get you started
  writing your own analyses.
* :ref:`How-to guides <dev_howto>` to help you with common tasks.
* :ref:`Developer's guides <dev_guides>` to help you understand how Cytoflow
  is structured (particularly useful for writing your own modules.)
* A :ref:`module reference <dev_reference>`, documenting all the user-facing
  classes, operations and views.

For Contributors
----------------

<<<<<<< Upstream, based on master
<<<<<<< Upstream, based on master
Hooray!  Have a look at the :ref:`install documentation <hacking>` for how to
get the source code installed.  Then, have a look at the  
:ref:`design docs <design>` and the :ref:`new modules <new_modules>` documentation.
Finally, join us over at 
`the cytoflow GitHub repo <https://github.com/cytoflow/cytoflow>`_ to file bugs, submit PRs, etc.
=======
Hooray!  We'd love to have you.
>>>>>>> 9522eaf docs: refactor documentation (in progress)
=======
The `Cytoflow source code <https://github.com/bpteague/cytoflow>`_ is hosted
over at `GitHub <https://github.com/>`_.  Feel free to report bugs, request
enhancements, fork the codebase and start hacking.  Also, check out the 
:ref:`Developers' guides <dev_guides>` for an overview and justification of
Cytoflow's design, as well as useful information for writing your own
modules, operations and views.
>>>>>>> e2b029c Docs: structure for users' and developers' manuals.


.. toctree::
   :hidden:
   
   user_manual/user_manual   
   dev_manual/dev_manual
   

   

   