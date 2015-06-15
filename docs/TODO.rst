Major features still TODO
-------------------------
* The GUI is still very much in flux.  Suggest letting me (Brian) work on it
  and contributing to the cytoflow library, at least until version 0.2.
  
* Installation may be a little hairy.  Please document your process.  The
  dependencies are laid out in README.md; if that list is incomplete, please
  update it.
  
* When we move to distribute this as an application, we'll have to figure out
  packaging.  (>= 0.3)
   
* May want to include import code locally, instead of depending on
  FlowCytometryTools.

* IPython notebook export.  Will depend on what a "workflow" looks like, which
  will be in the GUI, not the cytoflow package.
  
* pandas is great, but large data sets are likely to be kind of slow, especially
  for exploratory data analysis.  Implement some sort of feature to import only
  a subset of the data, then re-run the analysis on the whole data set once
  the workflow is established.  (May be a GUI thing, not a cytoflow thing....?)

* Operations

  * Gates: for formal definitions see http://flowcyt.sourceforge.net/gating/latest.pdf
  
    * 1D range gate
    * 2D rectangular gate
    * 2D quad gate
    * 2D polygon gate
    * 2D ellipsoid gate: data-driven, estimated from a centroid and a 2D 
      gaussian fit
      
  * Transformations (also see http://flowcyt.sourceforge.net/gating/latest.pdf )
  
    * Logicle: currently uses SWIG to wrap a C++ implementation.  Either
      figure out a way to build and distribute native code for Win32, Win64, OSX,
      Linux32, Linux64, OR do a full Python implementation.
    * Hyperlog: currently uses FlowCytometryTools' implementation.  
      Include locally?
    * Log transform
    * Asinh transform
    * Ratio transform (creates a new channel Z from channels X and Y, Z=X/Y)
    
  * Compensation: traditional matrix-based (both square and non-square)
  * Compensation: measured bleed-through (TASBE-like)
  
    * Need both *estimation from data* and *application to a data set*
    
  * 1D mixture model (from EM clustering)
  * K-means clustering?  May want to check out the "fcm" Python package
  * Binning (probably log-scale?)
  * Principle component analysis?
 
* Views

  * I'm still learning the matplotlib API.  For the moment, using the stateful
    API (pyplot) is fine, but we may move away from it to the Artist API soon.
    Will depend heavily on what the GUI interaction looks like.
  * General cleanup and beautification
  * Some well-thought-out interface for specifying graphical elements like colors
  * Histogram: add color-by-metadata attribute
  * 1D kernel density plot
  * 2D scatter plot
  
    * Want "backgating" ability, ie specify color by some gate metadata)
    
  * 2D hex bin plot (prettier than a scatter, faster than a density estimation)
  * 2D density plot
  * Stats plot: bar graph
  
    * Attribute: the statistic you're measuring (mean, count, variance, etc.)
    * Attribute: the channel you're measuring it on
    * Attribute: the condition for the X axis
    * Attribute: the condition for grouping (optional)
    * Attribute: x, y  trellis (optional)
    
  * Stats plot: xy plot

    * Attribute: x statistic
    * Attribute: x statistic channel
    * Attribute: y statistic
    * Attribute: y statistic channel
    * Attribute: x, y, hue trellis

  * Radar plots!  I just discovered these.  Possibly with principle component analysis?

    
