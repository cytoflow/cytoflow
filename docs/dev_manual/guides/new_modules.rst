.. _dev_new_modules:

Writing new ``cytoflow`` modules
================================

Creating a new module in :mod:`cytoflow` ranges from easy (for simple things)
to quite involved.  I like to think that :mod:`cytoflow` follows the Perl 
philosophy of making the easy jobs easy and the hard jobs possible.

With that in mind, let's look at the process of creating a new module,
progressing from easy to involved.

Basics
------

All the APIs (both public and internal) are built using
`Traits <http://docs.enthought.com/traits/>`_.  For operations and views in 
the :mod:`cytoflow` package, basic working knowledge of :mod:`traits` is sufficient.
For GUI work, trait notification is used extensively.

The GUI wrappers also use `TraitsUI <http://docs/enthought.com/traitsui/>`_ 
because it makes wrapping traits with UI elements easy.  Have a look at 
documentation for views, handlers, and of course the trait editors. 

Finally, there are some principles that I expect new modules contributed to this
codebase to follow:

* **Check for pathological errors and fail early**.  I really dislike the 
  tendency of a number of libraries to fail with cryptic errors.  (I'm looking at
  you, :mod:`pandas`.)  Check for obvious errors and raise a :class:`.CytoflowOpError`
  or :class:`.CytoflowViewError`).  If the problem is non-fatal, warn with
  :class:`.CytoflowOpWarning` or :class:`.CytoflowViewWarning`.  The GUI will
  also know how to handle these gracefully.
  
* **Separate experimental data from module state.**  There are workflows that
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
--------------

The base operation API is fairly simple:

* :attr:`~.IOperation.id` - a required :class:`traits.Constant` containing the UID of the operation

* :attr:`~.IOperation.friendly_id` - a required :class:`traits.Constant` containing a human-readable name

* :meth:`~.IOperation.apply` - takes an :class:`.Experiment` and returns a new
  :class:`.Experiment` with the operation applied.  :meth:`~.IOperation.apply` 
  should :meth:`~.Experiment.clone` the old experiment, then modify and return the 
  clone.  Don't forget to add the operation to the new :class:`.Experiment`'s 
  :attr:`~.Experiment.history`.  A good example of a simple operation is 
  :class:`.RatioOp`.
  
  .. note:: Be aware of the ``deep`` parameter for :meth:`~.Experiment.clone`!  It
            defaults to ``True`` -- **only** set it to ``False`` if you are only
            adding columns to the :class:`~.Experiment`.
  
* :meth:`~.IOperation.estimate` - You may also wish to estimate 
  the operation's parameters from a data set. Crucially, this 
  *might not be the data set you are eventually applying the operation to.*  If
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
---------

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
------------------
 
Wrapping an operation for the GUI sometimes feels like it requires more work
than writing the operation in the first place.  A new operation requires at
least five things:

* A class derived from the underlying :mod:`cytoflow` operation.  The derived
  operation should be placed in a module in :mod:`cytoflowgui.workflow.operations`,
  and it should:
  
  - Inherit from :class:`~.WorkflowOperation` to add support for various GUI
    event-handling bits (as well as the underlying :mod:`cytoflow` class,
    if appropriate)
    
  - Override attributes in the underlying :mod:`cytoflow` class to add
    metadata that tells the GUI how to react to changes.  (See the 
    :class:`~.IWorkflowOperation` docstring for details.)
    
  - Provide an implementation of :meth:`~.PluginOpMixin.get_notebook_code`, to
    support exporting to Jupyter notebook.
    
  - If the module has an :meth:`estimate` method, then implement 
    :meth:`clear_estimate` to clear those parameters.
    
  - If the module has a :meth:`default_view` method, it should be overridden
    to return a GUI-enabled view class (see below.)
    
  - Optionally, override :meth:`~.PluginOpMixin.should_apply` and 
    :meth:`~.PluginOpMixin.should_clear_estimate` to only do expensive operations
    when necessary.
    
* Serialization logic.  :mod:`cytoflow` uses :mod:`camel` for sane YAML 
  serialization; a dumper and loader for the class must save and load the
  operation's parameters.  These should also go in :mod:`cytoflowgui.workflow.operations`.

* A handler class that defines the default :class:`traits.View` and provides
  supporting logic.  This class should be derived from :class:`.OpHandler`
  and should be placed in :mod:`cytoflowgui.op_plugins`.
  
* A plugin class derived from :class:`envisage.plugin.Plugin` and implementing 
  :class:`.IOperationPlugin`.  It should also derive from :class:`.PluginHelpMixin`, 
  which adds support for online help.
  
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
-------------

A new view operation requires at least five things:

* A class derived from the underlying :mod:`cytoflow` view.  The derived
  view should be placed in :mod:`cytoflowgui.workflow.views`
  
  - Inherit from :class:`~.WorkflowView` or one of its children to add support 
    for various GUI event-handling bits
    
  - Override attributes in the underlying :mod:`cytoflow` class to add
    metadata that tells the GUI how to react to changes.  (See the 
    :class:`~.IWorkflowView` docstring for details.)
     
  - Provide an implementation of :meth:`~.PluginViewMixin.get_notebook_code`, to
    support exporting to Jupyter notebook.

  - Optionally, override :meth:`~.PluginViewMixin.should_plot` to only plot when
    necessary.
    
* Serialization logic.  :mod:`cytoflow` uses :mod:`camel` for sane YAML 
  serialization; a dumper and loader for the class must save and load the
  operation's parameters.  These should also go in :mod:`cytoflowgui.workflow.views`.

* A handler class that defines the default :class:`traits.View` and provides
  supporting logic.  This class should be derived from :class:`.ViewHandler`
  and should be placed in :mod:`cytoflowgui.view_plugins`.

* A plugin class derived from :class:`envisage.plugin.Plugin` and implementing 
  :class:`.IViewPlugin`.  It should also derive from :class:`.PluginHelpMixin`, 
  which adds support for online help.
  
* Plot parameters.  The parameters to a view's :meth:`plot` method are stored
  in an object that derives from :class:`BasePlotParams` or one of its 
  decendants.  Choose data types that are appropriate for the view, and
  include a default view named ``view_params_view`` in the handler class. 
  Don't forget to write serialization code for it as well!

* Tests.  Because of :mod:`cytoflowgui`'s split between processes, testing
  GUI logic for modules can be kind of a synchronization nightmare.  This is
  by design -- because the same synchronization issues are present when
  running the software.  See the ``cytoflowgui/tests`` directory for (many)
  examples.  In the case of a view, most of these are "smoke tests", testing
  that the view doesn't crash with various sets of parameters.
  
  
.. note:: Why the split between the classes in :mod:`cytoflowgui.op_modules`,
          :mod:`cytoflowgui.workflow.operations`, :mod:`cytoflowgui.view_modules`,
          and :mod:`cytoflowgui.workflow.views`?  It's because of the fact that
          ``cytoflow`` runs in two processes -- one handles the GUI and the other
          operates on the workflow. If you load a module containing UI bits, even
          if you don't explicitly create a ``QGuiApplication``, it starts an 
          event loop.  That's why older versions of ``Cytoflow`` had two icons
          in the task bar when running on a Mac.  You know how sometimes you go
          to fix a "little" bug and end up re-writing the whole program?  This
          was one of those times....


