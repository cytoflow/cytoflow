#CytoFlow
##Python tools for quantitative, reproducible flow cytometry analysis

Welcome to a different style of flow cytometry analysis.  Take a look at some example [Jupyter](http://jupyter.org/) notebooks:

* [Basic flow cytometry analysis](https://github.com/bpteague/cytoflow/blob/master/docs/examples-basic/Basic%20Cytometry.ipynb)
* [An small-molecule induction curve with yeast](https://github.com/bpteague/cytoflow/blob/master/docs/examples-basic/Yeast%20Dose%20Reponse.ipynb)
* [Data-driven gating with gaussian mixture models](https://github.com/bpteague/cytoflow/blob/master/docs/examples-basic/Machine%20Learning.ipynb)
* [Reproduced some analysis from a published paper](https://github.com/bpteague/cytoflow-examples/blob/master/kiani/Kiani%20Nature%20Methods%202014.ipynb)
* [Calibrated flow cytometry in MEFLs](https://github.com/bpteague/cytoflow-examples/blob/master/tasbe/TASBE%20Workflow.ipynb)

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

* **Free and open-source.**  Use the software free-of-charge; modify it to
  suit your own needs, then contribute your changes back so the rest of the
  community can benefit from them.

* Provides both **Python modules** (relatively complete) and a 
  **point-and-click interface** (still in development) 

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

* **Versatile.**  Built on Python, with a well-defined
  library of operations and visualizations that are well separated from
  the user interface.  Need an analysis that CytoFlow doesn't have?  Export 
  your workflow to an IPython notebook and use any Python module you want to 
  complete your analysis.  Data is stored in a pandas.DataFrame, which is 
  rapidly becoming the standard for Python data management (and will make R
  users feel right at home.)
  
* **Extensible.**  Adding a new analysis module is simple; the interface to
  implement is only two or three functions.

* **Quantitative and tatistically sound.** Ready access to useful data-driven tools for
  analysis, such as fitting 2-dimensional Gaussians for automated gating
  and mixture modeling.  ``cytoflow`` discourages (but does not prevent) wholesale
  rescaling of data, for example using the ``log10`` operation.  Instead, it
  encourages rescaling of the data's **plots** instead.

#### Note: this is still beta software!  Caveat emptor!
  
### Installation

See the [installation notes](http://cytoflow.readthedocs.org/en/latest/INSTALL.html) on [ReadTheDocs](http://cytoflow.readthedocs.org/).  Installation has been tested
on Linux (Ubuntu Trusty) and Windows 7 (x86_64).  Mac installation should be similar.

### Documentation

There is some basic documentation at [ReadTheDocs](http://cytoflow.readthedocs.org/).
Perhaps of most use is the [module index](http://cytoflow.readthedocs.org/en/latest/py-modindex.html).
The example [Jupyter](http://jupyter.org/) notebooks, above, demonstrate how the package
is intended to be used interactively.

### Required packages

These are all in the `setuptools` spec.

For the core `cytoflow` library, you need the following Python packages:
```
python >= 2.7
pandas >= 0.17.0
numpy >= 1.9.0
numexpr >= 2.1
bottleneck >= 1.0
matplotlib == 1.4.3
scipy >= 0.14
scikit-learn >= 0.16
seaborn >= 0.7.0
traits >= 4.0
fcsparser >= 0.1.1
```

For the GUI, you additionally need:
```
pyface == 4.4.0
envisage >= 4.0
pyqt >= 4.10 -- this must be installed separately!
```

Note that many of these packages have additional dependencies, including
but not limited to `traitsui`, `decorator`, etc.
Everything except PyQT should be a well well-behaved PyPI package; you should be
able to install all the above with `pip install` or the Canopy package manager.

