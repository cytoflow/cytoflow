.. _todo:

Major features still TODO
-------------------------
* Installation may be a little hairy.  Please document your process; current
  efforts are in :ref:`INSTALL.rst <install>`.  If you follow those 
  directions and it doesn't work, please submit a bug report; if you figure 
  out installation on a platform that's not there, please document your 
  process.
  
* IPython notebook export.  There is a branch by Guillermo Vargas, but it's
  not yet merged (and quite stale at this point.)

* A better export dialog.  At the moment, we call matplotlib's 
  ``canvas.print_figure``, which saves exactly what's on the screen.  
  That's .... suboptimal.  Maybe this could be combined with printing support?
  Would be nice to allow for choosing size, looking at preview.  Possibly another
  PyFace task, or at least some sort of modal dialog.  Try to piggy back off
  the plotting options GUI work (below).
  
* Support for more plotting options in the GUI.  The plan: add a tab to the
  view panel (maybe?) that lets you fiddle with two things: parameters that get
  passed to the various matplotlib plotting fuctions (that can be specified
  by each plotting module) and parameters that are plot-wide and get specified
  via the pyplot interace after a plot is created.  (These will be program-wide.)
  
* Better support for statistics.  This is the next thing on BT's plate to 
  implement.  This plan is still evolving, but it is
  currently: each module that can compute statistics adds them to the Experiment
  when apply() is called.  Each statistic is a Series, where the index is
  the groups from groupby() specifying the subsets on which the statistics
  were computed.  These Series are stored in a 
  (Instance(IOperation), String) --> Series dictionary, where the IOperation 
  is the operation that computed the statistic and the String is the name
  of the statistic (because some operations can make multiple statistics!).
  Will need to add a new module to compute basic 1-dimensional statistics 
  (are there interesting multidimensional statistics too?  Like R^2?  Hrm.)
  Plots and analyses that consume statistics must do something (facet or axis
  or error bars) with EVERY LEVEL of the Series index.  Subsets: keep track
  of which subset was used to compute a statistic and when analyzing or plotting
  multiple statistics, warn (but don't die!) if the subsets are different.
  
* For the GUI -- an online HELP function.  Something cross-platform, please?

* Operations
  * Asinh scale
     - It's not clear that we need this.  What do we gain over log & logicle?
       At least there's now a nice clean way to do this 
       (see ``cytoflow.utility.logicle_scale``)
  * Ratio transform (creates a new channel Z from channels X and Y, Z=X/Y)
     - If you're using the notebook, you can call add_channel().  
  * K-means clustering?  There's a branch, but it's not merged.
  * Principle component analysis?
 
* Views

  * General cleanup and beautification
  * Radar plots!  I just discovered these.  Possibly with principle component 
    analysis?

    
