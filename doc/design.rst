
a few design notes:

 - want to export an IPython notebook of the analysis.  both for easy human-
   readable record-keeping, and also because it's the ultimate in 
   extensibility: if the tool doesn't do what you want, use it for basic
   setup and data transformation, then use pure IPython to do what you need.
   
 - this makes the internal API really important: it has to be easy, intuitive
   and "pythonic" to 
   * get at data
   * apply operations to data
   * view / plot data
   
 - this probably means that the "internal" API is the same as the "external"
   API - ie, we're writing a package/library to analyze flow data, and then
   a nice UI around it.
   
 - in a perfect world, the execution of the analysis pipeline would be exactly
   the same python code (via exec()) as what's outputted to the notebook.
   
 - data representation:
   * invariants:
     - each tube or well was collected with the same channels and cytometer 
       settings
       (verify this on import!)
     - the number of events in an experiment never changes size.
   * an Experiment is a smart pandas DataFrame:
     - an Experiment begins as a concatenation of all of the events 
       in all of the tubes/wells
       * each channel is a column of dtype=float64
     - additional metadata is specified in additional columns
       * metadata can be numeric: ie, ex[ex['Dox'] == 0.5]
       * metadata can be categorical: ie, ex[ ex['Row'] == 'A' ]
     - allows for easy subsetting and plotting.
   * Experiments have operations applied to them; the application of an 
     operation to one experiment returns a new experiment
     - this allows Experiments to be smart about memory management:
       * a gate returns an Experiment that looks like the old one, but with an
         additional column of metadata describing population membership
       * a transformation returns an Experiment the same as the old one, but 
         with the transformed channels replacing the old columns (named the
         same)
   * Experiments are versioned
     - print( ex.version() )   # 1
       op = Transform(params)
       ex = ex.apply(op)
       print( ex.version() )  # 2
     - version #1 keeps a link to version #2
       * allows for invalidation; if #1 gets changed, #1 can invalidate #2
   * experiments keep track of useful data for plotting
     - ie, if you do a transformation, the experiment keeps track of the
       transform parameters so a view can draw axes appropriately.
       
 - basic workflow:
   * data import; creation of Experiment ex.
   * for each operation:
     - Create and parameterize the operation
     - Apply the operation
     - Create a view of the result
     
 - views
   * each view draws to either a WxAgg canvas or the IPython notebook
   * for each view
     - plot-type specifies what to be done with channels 
       * ie, specify one channel for a histogram; two for an xy plot
     - for each metadata column (not including plate pos!)
       * use to specify either a data subset or a plot grouping
       * if subset
         - if numerical, specify a range (with sliders)
         - if categorical, draw on/off buttons for categories
       * if plot grouping, use variable to specify plot params
         - x and y trellis: multiple plots with different vars
         - group: multiple lines or colors on a plot
   * view parameters exposed as Traits (to make UI easy)
   * Types of view:
     - histogram
       * param: channel for x axis; 
       * param: x trellis (meta or off)
       * param: y trellis (meta or off)
       * param: color (meta or off)
       * make sure to set a reasonable alpha transparency
     - xy plot (sns hexplot)
       * param: channel for x axis;
       * param: channel for y axis; 
       * param: x trellis (meta or off)
       * param: y trellis (meta or off)
       * param: color (meta or backgating or off)
         - if "backgating" - uh ..... ?
     - binned xy plot
       * same as above
     - bar graphs
       * param: statistic you're measuring
       * param: x axis (meta)
       * param: group (meta or off)
       * param: x trellis (meta or off)
       * param: y trellis (meta or off)
     - stats xy plot
       * param: x statistic
       * param: y statistic
       * param: x axis (meta)
       * param: y axis (meta)
       * param: group (meta or off)
       
 - operations
   * an operation is instantiated with parameters, then applied to an Experiment
     - an operation's parameters may include an Experiment, if it's data-driven
       (eg, a data-driven gating, mixture modelling, etc.)
   * an operation may return a default view based on the type of operation
     - ie, a range gate may return a histogram; 
       a poly or quad gate will return an xy plot
     - if this view has additional visual elements, it will be a subclass
       of the regular view.  this will also allow tighter integration with
       the operation, ie. to fix particular parameters.
     - for example, a 1D gate operation will have a default view with the
       gate drawn on top of it
   * interactivity
     - interactive default views will have a transparent widget drawn on top
       of them
     - manipulating the widget will update the view and the parameterization
       of the operation
   * operations
     - transformations
     - gates (user-drawn)
     - gates (data-driven)
     - mixture models
     - color model determination
     - color model application
     - bleedthrough correction  