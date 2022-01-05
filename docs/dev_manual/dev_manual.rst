.. _dev_manual:

################
Developer Manual
################

So you want to use `cytoflow` in your own Python-based analyses.
Great!  May I recommend you start with the :ref:`tutorials <dev_tutorials>`
and :ref:`examples <dev_examples>` -- they will give you a feel for 
the kinds of things you can use `cytoflow` to do.  All of them are
generated from `Jupyter notebooks <https://jupyter.org/>`_, and those
notebooks and data can be found in the ``Releases`` tab
at `the project homepage <https://github.com/cytoflow/cytoflow/>`_ 
(look for ``cytoflow-$VERSION-examples-basic.zip`` and
``cytoflow-$VERSION-examples-advanced.zip``).

Then, if you decide you want to have a go, see the 
:ref:`installation notes <install>`.  Quick hint: if you have Anaconda 
installed, say::

  conda config --add channels cytoflow
  conda create --name cytoflow cytoflow 
  
This creates a new Anaconda environment named ``cytoflow`` and installs the 
latest `cytoflow` package from the Anaconda Cloud.

For more details of these modules, you're likely to want to see the 
:ref:`module documents <modindex>`


*********
Contents:
*********

.. toctree::
   :maxdepth: 2

   tutorials/tutorials
   
   examples/examples
   
   howto/howto
   
   guides/guides
   
   faq
   
   api/cytoflow
   api/cytoflowgui
   
   
   
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
