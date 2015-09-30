Major features still TODO
-------------------------
* The GUI is still in flux.  Suggest letting me (Brian) work on it
  and contributing to the cytoflow library, at least until version 0.2.
  
* Installation may be a little hairy.  Please document your process; current
  efforts are in ``docs/INSTALL.rst``.  If you follow those directions and it
  doesn't work, please submit a bug report; if you figure out installation on
  a platform that's not there (anything other than Windows and Ubuntu), please
  document your process.
  
* When we move to distribute this as an application, we'll have to figure out
  packaging more thoroughly.  (>= 0.3)

* IPython notebook export.  Will depend on what a "workflow" looks like, which
  will be in the GUI, not the cytoflow package.

* Operations

  * Gates: for formal definitions see http://flowcyt.sourceforge.net/gating/latest.pdf

    * 2D quad gate
    * 2D ellipsoid gate: data-driven, estimated from a centroid and a 2D 
      gaussian fit
      
  * Transformations (also see http://flowcyt.sourceforge.net/gating/latest.pdf )
  
    * Asinh transform
    * Ratio transform (creates a new channel Z from channels X and Y, Z=X/Y)
    
  * Compensation: traditional matrix-based (both square and non-square)
    
  * 1D mixture model (from EM clustering)
  * K-means clustering?  May want to check out the "fcm" Python package
  * Principle component analysis?
 
* Views

  * Using ``seaborn`` for faceting means we're stuck with the stateful 
    ``matplotlib`` API (``pyplot``).  GUI integration was pretty smooth; 
    but some day it might be nice to move to ``Bokeh``.
  * General cleanup and beautification
  * Some well-thought-out interface for specifying graphical elements like colors
  * 1D kernel density plot
  
    * Want "backgating" ability, ie specify color by some gate metadata)
    
  * Prettier 2D hex bin plot (currently some issues with ``seaborn`` and faceting)
  * 2D density plot

  * Radar plots!  I just discovered these.  Possibly with principle component analysis?

    
