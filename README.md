#CytoFlow
##Python tools for quantitative, reproducible flow cytometry analysis

Welcome to a different style of flow cytometry analysis.  

### What's wrong with other packages?  

Packages such as FACSDiva and FlowJo are focused on primarily on identifying
and counting subpopulations of cells in a multi-channel flow cytometry
experiment.  While this is important for many different applications, it
reflects flow cytometry's origins in separating mixtures of cells based on
differential staining of their cell surface markers.

Cytometers can also be used to measure internal cell state, frequently as
reported by fluorescent proteins such as GFP.  In this context, they function
in a manner similar to a high-powered plate-reader: instead of reporting the
sum fluorescence of a population of cells, the cytometer shows you the
*distribution* of the cells' fluorescence.  Thinking in terms of distributions,
and how those distributions change as you vary an experimental variable, is
something existing packages don't handle gracefully.

### What's different about CytoFlow?

A few things.

* An emphasis on **metadata**.  CytoFlow assumes that you are measuring
  fluorescence on several samples that were treated differently: either
  they were collected at different times, treated with varying levels
  of inducers, etc.  You specify the conditions for each sample up front,
  then use those conditions to facet the analysis.

* Cytometry analysis conceptualized as a **workflow**.  Raw cytometry data
  is usually not terribly useful: you may gate out cellular debris and 
  aggregates (using FSC and SSC channels), then compensate for channel
  bleed-through, and finally select only transfected cells before actually
  looking at the parameters you're interested in experimentally.  CytoFlow
  implements a workflow paradigm, where operations are applied sequentially;
  a workflow can be saved and re-used, or shared with your coworkers.

* **Easy to use.**  Sane defaults; good documentation; focused on doing one
  thing and doing it well.

* **Good visualization.**  I don't know about you, but I'm getting really
  tired of FACSDiva plots.

* **Powerful and extensible.**  Built on Python, with a well-defined
  library of operations and visualizations that are well separated from
  the user interface.  Need new functionality?  Export your workflow to
  an IPython notebook and use any Python module you want to complete
  your analysis.

* **Statistically sound.** Ready access to useful data-driven tools for
  analysis, such as fitting 2-dimensional Gaussians for automated gating
  and mixture modelling.

## 


 
