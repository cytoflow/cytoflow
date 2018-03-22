.. _new_modules:

********************************
Writing new ``cytoflow`` modules
********************************

Creating a new module in ``cytoflow`` ranges from easy (for simple things)
to quite involved.  I like to think that ``cytoflow`` follows the Perl 
philosophy of making the easy jobs easy and the hard jobs possible.

With that in mind, let's look at the process of creating a new module,
progressing from easy to involved.

Basics
======

All the APIs (both public and internal) are built using
`Traits <http://docs.enthought.com/traits/>`_.  For operations and views in 
the :mod:`cytoflow` package, basic working knowledge of :mod:`traits` is sufficient.
For GUI work, trait notification is used extensively.

The GUI wrappers also use `TraitsUI <http://docs/enthought.com/traitsui/>`_ 
because it makes wrapping traits with UI elements easy.  Have a look at views,
handlers, and of course the trait editors. 

Finally, there are some principles that I expect new modules contributed to this
codebase to follow:

* **Check for pathological errors and fail early**.  I really dislike the 
  tendency of a number of libraries to fail with cryptic errors (I'm looking at
  you, :mod:`pandas`.)  Check for obvious errors and raise a :class:`.CytoflowOpError`
  or :class:`.CytoflowViewError`).  If the problem is non-fatal, warn with
  :class:`.CytoflowOpWarning` or :class:`.CytoflowViewWarning`.  The GUI will
  also know how to handle these gracefully.
  
* **Separate experimental data from module state.**  There are workflow that
  require estimating parameters with one data set, then applying those
  operations to another.  Make sure your module supports them.
  
* **Estimate slow but apply fast.**  The GUI re-runs modules' 
  :meth:`~.IOperation.apply` methods automatically when parameters change.
  That means that the :meth:`~.IOperation.apply` method must run very quickly.
  
* **Write tests.**  I hate writing unit tests, but they are indispensible for
  catching bugs.  Even in a view's tests are just smoke tests ("It plots something
  and doesn't crash"), that's better than nothing. 

.. _new_operation:

New operations
==============

The base operation API is fairly simple:

* :attr:`~.IOperation.id` - a required :class:`traits.Constant` containing the UID of the operation

* :attr:`~.IOperation.friendly_id` - a required :class:`traits.Constant` containing a human-readable name

* :meth:`~.IOperation.apply` - takes an :class:`.Experiment` and returns a new
  :class:`.Experiment` with the operation applied.  :meth:`~.IOperation.apply` 
  should :meth:`~.Experiment.clone` the old experiment, then modify and return the 
  clone.  Don't forget to add the operation to the new :class:`.Experiment`'s 
  :attr:`~.Experiment.history`.  A good example of a simple operation is 
  :class:`.RatioOp`.
  
* :meth:`~.IOperation.estimate` - You may also wish to estimate 
  the operation's parameters from a data set. Crucially, this 
  *may not be the data set you are eventually applying the operation to.*  If
  your operation relies on estimating parameters, implement the 
  :meth:`~.IOperation.estimate` function.  This may involve selecting a subset
  of the data in the :class:`.Experiment`, or it may involve loading in an
  an additional FCS file. A good example of the former is :class:`.KMeansOp`; 
  a good example of the latter is :class:`.AutofluorescenceOp`.
  
  You may also find that you wish to estimate different parameter sets for 
  different sub-populations (as encoded in the :class:`.Experiment`'s 
  :attr:`~.Experiment.conditions`.)  By convention, the conditions that you 
  want to estimate different parameters for are passed using a trait named 
  :attr:`by`, which takes a list of conditions and groups the data by unique
  combinations of those conditions' values before estimating a paramater set
  for each.  Look at :class:`.KMeansOp` for an example of this behavior.
  
* :meth:`~.IOperation.default_view` - for some operations, you may want to 
  provide a default view.  This view may just be a base view parameterized in
  a particular way (like the :class:`.HistogramView` that is the default view of
  :class:`.BinningOp`), or it may be a visualization of the parameters estimated
  by the :meth:`~.IOperation.estimate` function (like the default view of 
  :class:`.AutofluorescenceOp`.)  In many cases, the view returned by this 
  function is linked back to the operation that produced it.
  
 
.. _new_view:
 
New views
=========

The base view API is very simple:

* :attr:`~.IView.id` - a required :class:`traits.Constant` containing the UID of the operation

* :attr:`~.IView.friendly_id` - a required :class:`traits.Constant` containing a human-readable name

* :meth:`~.IView.plot` - plots :class:`.Experiment`.

As I wrote more views, however, I noticed a significant amount of code
duplication, which led to bugs and lost time.  So, I refactored the view code
to use a short hierarchy of classes for particular types of views.  You can
take advantage of this functionality when writing a new module, or you can
simply derive your new view from :class:`traits.HasTraits` and implement the
simple API above.

The view base classes are:

* :class:`.BaseView` -- implements a view with row, column and hue facets.
  After setting up the facet grid, it calls the derived class's 
  :meth:`_grid_plot` to actually do the plotting.  :meth:`~.BaseView.plot` also
  has parameters to set the plot style, legend, axis labels, etc.
  
* :class:`.BaseDataView` -- implements a view that plots an :class:`.Experiment`'s
  data (as opposed to a statistic.)  Includes functionality for subsetting
  the data before plotting, and determining axis limits and scales.
  
* :class:`.Base1DView` -- implements a 1-dimensional data view.  See 
  :class:`.HistogramView` for an example.
  
* :class:`.Base2DView` -- implements a 2-dimensional data view.  See
  :class:`.ScatterplotView` for an example.
  
* :class:`.BaseNDView` -- implements an N-dimensional data view.  See
  :class:`.RadvizView` for an example.
  
* :class:`.BaseStatisticsView` -- implements a view that plots a statistic from
  an :class:`.Experiment` (as opposed to the underlying data.)  These views
  have a "primary" :attr:`~.BaseStatisticsView.variable`, and can be subset
  as well.
  
* :class:`.Base1DStatisticsView` -- implements a view that plots one dimension
  of a statistic.  See :class:`.BarChartView` for an example.
  
* :class:`.Base2DStatisticsView` -- implements a view that plots two dimensions
  of a statistic.  See :class:`.Stats2DView` for an example.
  

.. _new_operation_plugin:


New GUI operations
==================
 
Wrapping an operation for the GUI sometimes feels like it requires more work
than writing the operation in the first place.  A new operation requires at
least five things:

* A plugin class implementing either :class:`.IOperationPlugin`.  It should 
  also derive from :class:`.PluginHelpMixin`, which adds support for online help.
  
* A class derived from the underlying :mod:`cytoflow` operation.  The derived
  operation should:
  
  - Inherit from :class:`PluginOpMixin` to add support for various GUI
    event-handling bits
    
  - Override attributes in the underlying :mod:`cytoflow` class to add
    metadata that tells the GUI how to react to changes.  (See the 
    :class:`.PluginOpMixin` docstring for details.)
    
  - Override the :attr:`~.PluginOpMixin.handler_factory` attribute to be a callable that returns
    an :class:`.OpHandlerMixin` instance.
    
  - Provide an implementation of :meth:`~.PluginOpMixin.get_notebook_code`, to
    support exporting to Jupyter notebook.
    
  - If the module has an :meth:`estimate` method, then implement 
    :meth:`clear_estimate` to clear those parameters.
    
  - If the module has a :meth:`default_view` method, it should be overridden
    to return a GUI-enabled view class (see below.)
    
  - Optionally, override :meth:`~.PluginOpMixin.should_apply` and 
    :meth:`~.PluginOpMixin.should_clear_estimate` to only do expensive operations
    when necessary.
    
* A handler class that defines the default :class:`traits.View` and provides
  supporting logic.  This class should be derived from :class:`.OpHandlerMixin`
  and :class:`traits.Controller`.
  
* Serialization logic.  :mod:`cytoflow` uses :mod:`camel` for sane YAML 
  serialization; a dumper and loader for the class must save and load the
  operation's parameters.

* Tests.  Because of :mod:`cytoflowgui`'s split between processes, testing
  GUI logic for modules can be kind of a synchronization nightmare.  This is
  by design -- because the same synchronization issues are present when
  running the software.  See the ``cytoflowgui/tests`` directory for (many)
  examples.
  
* (Optionally) default view implementations.  If the operation has a default
  view, you should wrap it as well (in the operation plugin module.)  See the
  next section for details.
  
.. _new_view_plugin:

New GUI views
=============

A new view operation requires at least five things:


* A plugin class implementing either :class:`.IViewPlugin`.  It should 
  also derive from :class:`.PluginHelpMixin`, which adds support for online help.
  
* A class derived from the underlying :mod:`cytoflow` view.  The derived
  view should:
  
  - Inherit from :class:`.PluginViewMixin` to add support for various GUI
    event-handling bits
    
  - Override attributes in the underlying :mod:`cytoflow` class to add
    metadata that tells the GUI how to react to changes.  (See the 
    :class:`PluginViewMixin` docstring for details.)
    
  - Override the :attr:`~.PluginViewMixin.handler_factory` attribute to be a 
    callable that returns a :class:`.ViewHandlerMixin` instance.
    
  - Provide an implementation of :meth:`~.PluginViewMixin.get_notebook_code`, to
    support exporting to Jupyter notebook.

  - Override the :attr:`~PluginViewMixin.plot_params` attribute with an instance
    of an object containing plot parameters (see below).
    
  - Optionally, override :meth:`~.PluginViewMixin.should_plot` to only plot when
    necessary.
    
  - Optionally, overide :meth:`~.PluginViewMixin.plot_wi` to change whether
    :meth:`plot` is called on the current :class:`.WorkflowItem`'s result or
    the previous one's.
    
    
* A handler class that defines the default :class:`traits.View` and provides
  supporting logic.  This class should be derived from :class:`.ViewHandlerMixin`
  and :class:`traits.Controller`.
  
* Serialization logic.  :mod:`cytoflow` uses :mod:`camel` for sane YAML 
  serialization; a dumper and loader for the class must save and load the
  operation's parameters.
  
* Plot parameters.  The parameters to a view's :meth:`plot` method are stored
  in an object that derives from :class:`BasePlotParams` or one of its 
  decendants.  Choose data types that are appropriate for the view, and
  include a default view.  Set it as the class type for the view's :attr:`plot_params`
  attribute.  Don't forget to write serialization code for it as well!

* Tests.  Because of :mod:`cytoflowgui`'s split between processes, testing
  GUI logic for modules can be kind of a synchronization nightmare.  This is
  by design -- because the same synchronization issues are present when
  running the software.  See the ``cytoflowgui/tests`` directory for (many)
  examples.  In the case of a view, most of these are "smoke tests", testing
  that the view doesn't crash with various sets of parameters.