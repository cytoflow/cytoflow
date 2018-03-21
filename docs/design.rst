.. _design:

Project Structure
-----------------

The source is organized into two main components.

* The :mod:`cytoflow` package.  This package contains the actual tools for 
  operating on cytometry data.  Key modules and subpackages:

  * The :class:`~cytoflow.experiment.Experiment` class is the primary container for cytometry data. See
    the module docstrings for its use.  Modify this class's API only with care,
    please!  
    
  * The :mod:`cytoflow.operations` subpackage.  This is where operations on data go, like
    transformations and gates.  Adding a new operation is quite straightforward:
    see the documentation for :ref:`adding a new operation <new_operation>`.
    
  * The :mod:`cytoflow.views` subpackage.  This is where visualizations go.  These can be
    traditional visualizations (dotplots, histograms); or statistical summary
    views (bar plots of population means).  There is a significant amount of 
    class hierarchy here -- see the documentation for :ref:`adding a new view <new_view>`.
    
  * The :mod:`cytoflow.utility` subpackage.  Useful functions and classes, like
    :meth:`~cytoflow.utility.util_functions.geom_mean`.

* The :mod:`cytoflowgui` package.  Implements the GUI. 

  * The :mod:`cytoflowgui.op_plugins` subpackage.  Contains instances of 
    :class:`envisage.Plugin` that wrap the operations.  See the documentation 
    for :ref:`adding a new operation GUI plugin <new_operation_plugin>`.
    
  * The :mod:`cytoflowgui.op_views` subpackage.  Contains instances of 
    :class:`envisage.Plugin` that wrap the views.  See the documentation if you 
    want to :ref:`add a new view GUI plugin <new_view_plugin>`.


Design decisions & justifications
---------------------------------

* Cytometry analysis as a workflow -- an analysis is a set of operations
  applied sequentially to a dataset.  I think this is kind of obvious; it just
  formalizes the way of doing things that everyone else pretty much already
  uses.

* Instead of keeping "tubes" or "wells" as first-class objects, represent all
  the events from all the samples as a big long :class:`pandas.DataFrame`, 
  distinguishing events from different tubes via their varying experimental conditions.  Most
  of my flow analysis experience is with the R Bioconductor package's flowCore,
  which treats tubes as first-class objects akin to separate microarrays.
  That's fine if you've got just a few tubes (or a few microarrays), but it
  rapidly gets cumbersome if you've got multiple plates of samples, each plate
  of which has two or three experimental variables; I ended up spending more
  time and code specifying metadata than I did actually doing analysis.
 
  Cytoflow pushes the metadata down to the event level, doing away entirely
  with the concept of tubes or wells (after you get your data imported, of
  course.)  This hews much more closely to Hadley Wickham's concept of `Tidy
  Data <http://vita.had.co.nz/papers/tidy-data.pdf>`_, and is also (!) much
  easier to vectorize computations on using :mod:`pandas` and :mod:`numpy` and
  :mod:`numexpr`. Now, you can access all the events that are, say
  Dox-induced, by just saying ``experiment['Dox']`` without having to keep
  track of which tubes are induced and which weren't.

  .. note:: If you have tubes that are replicates, just add another experimental
     condition, perhaps called "replicate".  You can specify that condition to the
     statistics views to get a standard error.

* Gates don't actually subset data (delete or copy it); they just add metadata.
  I struggled for a long time with the question of how to store and manipulate
  different subsets of data after gating.  Again, my own experience is with
  Bioconductor's ``flowCore``, which defines a tree structure by data that is
  included or excluded by gates; if a node is a gate, then its children are the
  subpopulations produced by that gate. Navigating that tree, though, is really
  difficult, especially if you want to re-combine data after gating (for
  plotting, for example.)

  Then there was the issue of how to track and manipulate this structure as
  additional operations were performed.  Keep just a single copy and operate on
  it in-place?  Or copy the output of one operation for the input of the next,
  with the space penalties that implies?

  I finally realized I didn't have to choose; when you copy a 
  :class:`pandas.DataFrame`, you get a "shallow" copy, with the actual data just 
  linked to by reference.  This was perfect; if I needed to transform the data 
  from one copy to another, I could just replace the transformed channels; and 
  "gating" events didn't have to create new subsets or containers, it could 
  just add another column specifying the gate membership of each event.
  
* :mod:`cytoflow` discourages wholesale transformation of the underlying data, ie.
  taking the log of the data set.  This is of a part with :mod:`cytoflow` 
  enabling *quantitative* analysis -- if you want a measure of center of data 
  that is log-normal, you should use the geometric mean instead of log-transforming
  and taking the arithmetic mean.  It is frequently useful to transform data 
  before viewing it, or gating it, etc -- those transformations can be passed 
  as parameters to the view modules.

  The obvious exceptions here, of course, are things like bleedthrough
  correction and calibration using beads. These operations transform the data,
  but they don't cause the same sorts of shift in data *structure* you see with
  a log transform.  Data that is distributed log-normally before bleedthrough
  correction, will be distributed log-normally after.

* As is made pretty clear in the example Jupyter notebooks, the semantics for
  views and operations are

  1. Instantiate a new operation or view 

  2. Parameterize the operation or view (possibly by estimating parameters from
       a provided data set). 

  3. Apply the operation or view to an :class:`~cytoflow.experiment.Experiment`. 
     If applying an operation, :meth`apply` returns a new Experiment. 

  The justification for these semantics is that it makes the *state* of the
  interacting objects really obvious.  An operation or view's state doesn't
  depend on the data it's applied to; if its parameters do depend on data,
  those parameters' estimation is a separate operation.  

  It also allows for ready separation of the workflow from the data it's
  applied to, allowing for easy sharing of workflows.

* The module attributes have been replaced by Traits.  See the `Traits
  documentation <http://docs.enthought.com/traits/>`_ for a good overview, but
  in short they give Python some of the benefits of statically typed languages
  like Java, without much of the mess that a fully statically typed language
  incurs.  Their power doesn't see a whole lot of use internal to the cytoflow
  package, but they make writing the GUI layer a **whole** lot easier.

* The design of the views are strongly influenced by best-in-class statistics
  visualization packages from R: ``lattice`` and ``ggplot``.  If your data is
  `tidy <http://vita.had.co.nz/papers/tidy-data.pdf>`_, then each experimental
  variable you want to plot differently so you can compare them is called a
  "facet". For example, a facet might be a timepoint or an inducer level (ie an
  experimental condition); it might also be some metadata added by an operation
  (ie gate membership or bin).  Then, you plot the dataset broken down in
  various ways by its facets: for example, each timepoint might be put on its
  own subplot, while each Dox level might be represented by a different color.
  (Check out `the example Jupyter notebook
  <https://github.com/bpteague/cytoflow/blob/master/docs/examples-basic/Basic%20Cytometry.ipynb>`_
  if this is confusing.

