.. _todo:

Major features still TODO
-------------------------
* Installation may be a little hairy.  Please document your process; current
  efforts are in :ref:`INSTALL.rst <install>`.  If you follow those 
  directions and it doesn't work, please submit a bug report; if you figure 
  out installation on a platform that's not there, please document your 
  process.
  
* IPython notebook export.  There is a branch by Guillermo Vargas, but it's
  not yet merged.

* A better export dialog.  At the moment, we call matplotlib's 
  ``canvas.print_figure``, which saves exactly what's on the screen.  
  That's .... suboptimal.  Maybe this could be combined with printing support?

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
  * Some well-thought-out GUI interface for specifying graphical elements 
    like colors and axis labels.
  * Radar plots!  I just discovered these.  Possibly with principle component 
    analysis?

    
