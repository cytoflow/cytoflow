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
the ``cytoflow`` package, basic working knowledge of ``traits`` is sufficient.
For GUI work, trait notification is used extensively.

The GUI wrappers also use `TraitsUI <http://docs/enthought.com/traitsui/>`_ 
because it makes wrapping traits with UI elements easy.  Have a look at views,
handlers, and of course the trait editors. 


New operations
==============

The base operation API is fairly simple:

* ``id`` - a required ``Constant`` containing the UID of the operation

* ``friendly_id`` - a required ``Constant`` containing a friendly name

* ``apply(self, experiment`` - takes an ``Experiment`` and returns a new
  ``Experiment`` with the operation applied.  ``apply`` should ``clone()``
  the old experiment, then modify and return the clone.  Don't forget to
  add the operation to the new ``Experiment``'s ``history``.  A good example
  of a simple operation is ``RatioOp``.
  
* ``estimate(self, experiment, subset = None)`` - You may also wish to estimate 
  the operation's parameters from a data set. Crucially, this 
  *may not be the data set you are eventually applying the operation to.*  If
  your operation relies on estimating parameters, implement the ``estimate``
  function.  This should select a subset of the ``Experiment`` parameter, then
  estimate the operation parameters.  A good example of an operation that
  behaves this way is ``AutofluorescenceOp``.
  
  You may also find that you wish to estimate different parameter sets for 
  different sub-populations (as encoded in the ``Experiment``'s ``conditions``.)
  By convention, the conditions that you want to estimate different parameters
  for are passed using a trait named ``by``, which takes a list of conditions
  and groups the data by them before estimating a parameter set for each.
  Look at ``GaussianOp`` for an example of this behavior.
  
* ``default_view(self, **kwargs)`` - for some operations, you may want to 
  provide a default view.  This view may just be a base view parameterized in
  a particular way (like the ``HistogramView`` that is the default view of
  ``BinningOp``), or it may be a visualization of the parameters estimated
  by the ``estimate`` function (like the default view of ``AutofluorescenceOp``.)
  In many cases, the view returned by this function is linked back to the
  operation that produced it.
  
 