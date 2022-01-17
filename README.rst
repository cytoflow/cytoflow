Cytoflow
========

Python tools for quantitative, reproducible flow cytometry analysis
-------------------------------------------------------------------

Welcome to a different style of flow cytometry analysis. Take a look at
some example `Jupyter <http://jupyter.org/>`__ notebooks:

-  `Basic flow cytometry
   analysis <https://github.com/cytoflow/cytoflow/blob/master/docs/examples-basic/Basic%20Cytometry.ipynb>`__
-  `An small-molecule induction curve with
   yeast <https://github.com/cytoflow/cytoflow/blob/master/docs/examples-basic/Yeast%20Dose%20Response.ipynb>`__
-  `Machine learning applied to flow cytometry
   data <https://github.com/cytoflow/cytoflow/blob/master/docs/examples-basic/Machine%20Learning.ipynb>`__
-  `Reproduced analysis from a published
   paper <https://github.com/cytoflow/cytoflow-examples/blob/master/kiani/Kiani%20Nature%20Methods%202014.ipynb>`__
-  `A multi-dimensional induction in
   yeast <https://github.com/cytoflow/cytoflow-examples/blob/master/yeast/Induction%20Timecourse.ipynb>`__
-  `Calibrated flow
   cytometry <https://github.com/cytoflow/cytoflow-examples/blob/master/tasbe/TASBE%20Workflow.ipynb>`__

or some `screenshots from the
GUI <http://cytoflow.github.io/screenshots.html>`__

Note: My ‘day job’ is teaching at a regional comprehensive college, so during the semester I may not have a huge amount of time to respond to bugs and feature requests. I’m still activately developing Cytoflow, so please continue to file bugs!
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

What’s wrong with other packages?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Packages such as FACSDiva and FlowJo are focused on primarily on
identifying and counting subpopulations of cells in a multi-channel flow
cytometry experiment. While this is important for many different
applications, it reflects flow cytometry’s origins in separating
mixtures of cells based on differential staining of their cell surface
markers.

Cytometers can also be used to measure internal cell state, frequently
as reported by fluorescent proteins such as GFP. In this context, they
function in a manner similar to a high-powered plate-reader: instead of
reporting the sum fluorescence of a population of cells, the cytometer
shows you the *distribution* of the cells’ fluorescence. Thinking in
terms of distributions, and how those distributions change as you vary
an experimental variable, is something existing packages don’t handle
gracefully.

What’s different about Cytoflow?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A few things.

-  **Free and open-source.** Use the software free-of-charge; modify it
   to suit your own needs, then contribute your changes back so the rest
   of the community can benefit from them.

-  A `point-and-click interface <http://cytoflow.github.io/>`__ for easy
   analysis.

-  **Python modules** to integrate into larger apps, automation, or for
   use in a `Jupyter notebook <http://jupyter.org/>`__

-  An emphasis on **metadata**. Cytoflow assumes that you are measuring
   fluorescence on several samples that were treated differently: either
   they were collected at different times, treated with varying levels
   of inducers, etc. You specify the conditions for each sample up
   front, then use those conditions to facet the analysis.

-  Cytometry analysis conceptualized as a **workflow**. Raw cytometry
   data is usually not terribly useful: you may gate out cellular debris
   and aggregates (using FSC and SSC channels), then compensate for
   channel bleed-through, and finally select only transfected cells
   before actually looking at the parameters you’re interested in
   experimentally. Cytoflow implements a workflow paradigm, where
   operations are applied sequentially; a workflow can be saved and
   re-used, or shared with your coworkers.

-  **Easy to use.** Sane defaults; good documentation; focused on doing
   one thing and doing it well.

-  **Good visualization.** I don’t know about you, but I’m getting
   really tired of FACSDiva plots.

-  **Versatile.** Built on Python, with a well-defined library of
   operations and visualizations that are well separated from the user
   interface. Need an analysis that Cytoflow doesn’t have? Export your
   workflow to a Jupyter notebook and use any Python module you want to
   complete your analysis. Data is stored in a ``pandas.DataFrame``,
   which is rapidly becoming the standard for Python data analysis (and
   will make R users feel right at home.)

-  **Extensible.** `Adding a new analysis or visualization
   module <http://cytoflow.readthedocs.io/en/stable/new_modules.html>`__
   is simple; the interface to implement is only two or three functions.

-  **Quantitative and statistically sound.** Ready access to useful
   data-driven tools for analysis, such as fitting 2-dimensional
   Gaussians for automated gating and mixture modeling.

Installation
~~~~~~~~~~~~

**If you just want the point-and-click version (not the Python modules),
you can install it from http://cytoflow.github.io/**

See the `installation
notes <http://cytoflow.readthedocs.org/en/stable/INSTALL.html>`__ on
`ReadTheDocs <http://cytoflow.readthedocs.org/>`__. Installation has
been tested on Linux, Windows (x86_64) and Mac. Cytoflow is distributed
as an `Anaconda <https://www.anaconda.com/>`__ package **(recommended)**
as well as a `traditional Python
package <https://pypi.org/project/cytoflow/>`__.

Documentation
~~~~~~~~~~~~~

Cytoflow’s documentation lives at
`ReadTheDocs <http://cytoflow.readthedocs.org/>`__. Perhaps of most use
is the `module
index <http://cytoflow.readthedocs.org/en/latest/py-modindex.html>`__.
The example `Jupyter <http://jupyter.org/>`__ notebooks, above,
demonstrate how the package is intended to be used interactively.
