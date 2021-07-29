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
:ref:`screenshots <user_screenshots>`, or you can check out a 
`screencast on Youtube <https://www.youtube.com/watch?v=vfEfeFGVtro>`_.
  
Getting Started
---------------

Quick installation instructions for the point-and-click program:

* **Windows**: `Download the installer <https://cytoflow.github.io/>`_, 
  then run it.
* **MacOS (10.10+)**: `Download the ZIP file <https://cytoflow.github.io/>`_.  
  Unzip the file, then double-click to run the program.  Depending on your
  security settings, you may have to specifically enable this program 
  (it's not signed.)
* **Linux**: `Download the tarball <https://cytoflow.github.io>`_.
  Extract it, then run the *cytoflow* binary.
  
More detailed installation instructions :ref:`can be found in the user's manual. <user_install>`.

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


For Developers
--------------

If you want to use `Python <https://www.python.org/>`_ to analyze flow
cytometry data, then Cytoflow is for you!  I've found Cytoflow useful
for both *interactive data exploration* (ie, poking data to see what it's
telling you) and *automated data analysis* (ie, writing scripts and pipelines
to process lots of data.)  

To get a taste of what Cytoflow can do, check out an 
`example Jupyter notebook <https://github.com/cytoflow/cytoflow/blob/master/docs/examples-basic/Basic%20Cytometry.ipynb>`_.

Then, head over to the :ref:`developers' manual <dev_manual>`.  There,
you'll find:

* :ref:`Tutorial Jupyter notebooks <dev_tutorials>` to get you started
  writing your own analyses.
* :ref:`How-to guides <dev_howto>` to help you with common tasks.
* :ref:`Developer's guides <dev_guides>` to help you understand how Cytoflow
  is structured (particularly useful for writing your own modules.)
* An :doc:`API reference <dev_manual/api/cytoflow>`, documenting all the user-facing
  classes, operations and views.

For Contributors
----------------

Hooray!  We'd love to have you.

The `Cytoflow source code <https://github.com/cytoflow/cytoflow>`_ is hosted
over at `GitHub <https://github.com/>`_.  Feel free to report bugs, request
enhancements, fork the codebase and start hacking.  Also, check out the 
:ref:`Developers' guides <dev_guides>` for an overview and justification of
Cytoflow's design, as well as useful information for writing your own
modules, operations and views.


.. toctree::
   :hidden:
   
   user_manual/user_manual  
   dev_manual/dev_manual

   