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
  
* For the GUI -- an online HELP function.  Something cross-platform, please?

* Operations
  * K-means clustering?  There's a branch, but it's not merged.
  * Principle component analysis?
 
* Views

  * General cleanup and beautification
  * Radar plots!  I just discovered these.  Possibly with principle component 
    analysis?

    
