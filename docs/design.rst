Project Structure
-----------------

The source is organized into two main components.

* The ``cytoflow`` package.  This package contains the actual tools for operating on cytometry data.  Key modules and subpackages:

  * The ``Experiment`` class is the primary container for cytometry data. See the module docstrings for its use.  Modify this class's API only with care, please!
  * The ``operations`` subpackage.  This is where operations on data go, like transformations and gates.
  * The ``views`` subpackage.  This is where visualizations go.  These can be traditional visualizations (dotplots, histograms); or statistical summary views (bar plots of population means).
  * A ``utility`` subpackage.  Useful functions and classes, like ``geom_mean``.

* The ``cytoflowgui`` package.  Implements the GUI.  (Duh.)


Design decisions & justifications
---------------------------------
* Cytometry analysis as a workflow.  I think this is kind of obvious; it just formalizes the way of doing things that everyone else pretty much already uses.

* Instead of keeping "tubes" or "wells" as first-class objects, represent all the events from all the samples as a big long DataFrame, distinguishing events from different tubes via their varying experimental conditions.  Most of my flow analysis experience is with the R Bioconductor package's flowCore, which treats tubes as first-class objects akin to separate microarrays.  That's fine if you've got just a few tubes (or a few microarrays), but it rapidly gets cumbersome if you've got multiple plates of samples, each plate of which has two or three experimental variables; I ended up spending more time and code specifying metadata than I did actually doing analysis.
 
  Cytoflow pushes the metadata down to the event level, doing away entirely with the concept of tubes or wells (after you get your data imported, of course.)  This hews much more closely to Hadley Wickham's concept of `Tidy Data <http://vita.had.co.nz/papers/tidy-data.pdf>`_, and is also (!) much easier to vectorize computations on using ``pandas`` and ``numpy`` and ``numexpr``. Multicore FTW.  Now, you can access all the events that are, say Dox-induced, by just saying ``experiment['Dox']`` without having to keep track of which tubes are induced and which weren't.

  (Note: if you have tubes that are replicates, just add another experimental condition, perhaps called "replicate".  You can specify that condition to the statistics views to get a standard error.)

* Gates don't actually subset data (delete or copy it); they just add metadata. I struggled for a long time with the question of how to store and manipulate different subsets of data after gating.  Again, my own experience is with Bioconductor's ``flowCore``, which defines a tree structure by data that is included or excluded by gates; if a node is a gate, then its children are the subpopulations produced by that gate. Navigating that tree, though, is really difficult, especially if you want to re-combine data after gating (for plotting, for example.)

  Then there was the issue of how to track and manipulate this structure as additional operations were performed.  Keep just a single copy and operate on it in-place?  Or copy the output of one operation for the input of the next, with the space penalties that implies?

  I finally realized I didn't have to choose; when you copy a pandas.DataFrame, you get a "shallow" copy, with the actual data just linked to by reference.  This was perfect; if I needed to transform the data from one copy to another, I could just replace the transformed channels; and "gating" events didn't have to create new subsets or containers, it could just add another column specifying the gate membership of each event.

* As is made pretty clear in the example IPython notebook, the semantics for views and operations are

  1. Instantiate a new operation or view 

  2. Parameterize the operation or view (possibly by estimating parameters from a provided data set). 

  3. Apply the operation or view to an ``Experiment``. If applying an operation,
     ``apply()`` returns a new Experiment. 

  The justification for these semantics is that it makes the *state* of the interacting objects really obvious.  An operation or view's state doesn't depend on the data it's applied to; if its parameters do depend on data, those parameters' estimation is a separate operation.  

  It also allows for ready separation of the workflow from the data it's applied to, allowing for easy sharing of workflows. (Maybe.  I think.)

* The module attributes have been replaced by Traits.  See the `Traits documentation <http://docs.enthought.com/traits/>`_ for a good overview, but in short they give Python some of the benefits of statically typed languages like Java, without much of the mess that a fully statically typed language incurs.  Their power doesn't see a whole lot of use internal to the cytoflow package, but they make writing the GUI layer a **whole** lot easier.

* The design of the views are strongly influenced by best-in-class statistics visualization packages from R: ``lattice`` and ``ggplot``.  If your data is `tidy <http://vita.had.co.nz/papers/tidy-data.pdf>`_, then each experimental variable you want to plot differently so you can compare them is called a "facet". For example, a facet might be a timepoint or an inducer level (ie an experimental condition); it might also be some metadata added by an operation (ie gate membership or bin).  Then, you plot the dataset broken down in various ways by its facets: for example, each timepoint might be put on its own subplot, while each Dox level might be represented by a different color.  (Check out `the example IPython notebook <http://nbviewer.ipython.org/github/bpteague/cytoflow/blob/master/doc/examples/Basic%20Cytometry.ipynb>`_ if this is confusing.
