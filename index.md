---
layout: default
title: {{ site.name }}
---
# Welcome!  New to Cytoflow?  Start with a [tutorial.](https://cytoflow.readthedocs.io/en/stable/manual/01_quickstart.html)

# What's wrong with other packages?  

Packages such as FACSDiva and FlowJo are focused on primarily on **identifying
and counting subpopulations** of cells.  While this is important for many
different applications, it reflects flow cytometry's origins in separating
mixtures of cells based on differential staining of their cell surface markers.

Recent experiments in our lab and others have been more interested in
using a cytometer to **compare distributions** of cells, asking how these
distributions change in response to **experimental variables.** Existing
packages don't handle this gracefully!

# How is Cytoflow different?

* An emphasis on **metadata**.  Cytoflow assumes that you are measuring
  fluorescence on several samples that were treated differently: either
  they were collected at different times, treated with varying levels
  of inducers, etc.  You specify the conditions for each sample up front,
  then use those conditions to control the analysis.

* Cytometry analysis represented as a **workflow**. Operations such as
  gating and compensation are applied sequentially; a workflow can be 
  saved and re-used, or shared with your coworkers.

* **Easy to use.**  Sane defaults; good documentation; focused on doing one
  thing and doing it well.

* **Good visualization.**  I don't know about you, but I'm getting really
  tired of FACSDiva plots.

* The point-and-click interface is built on **Python modules**.  Do you 
  analyze data with Python?  If so, head over to the 
  [developer documentation](https://cytoflow.readthedocs.io/) to use these 
  modules in your own workflow.  They have been designed to work well in a 
  [Jupyter notebook](http://jupyter.org/); in fact, the GUI will even export 
  a workflow directly to a notebook!

* **Free and open-source.**  Download the source code from 
  [the GitHub project page](https://github.com/bpteague/cytoflow) and modify it 
  to suit your own needs, then contribute your changes back so the rest of 
  the community can benefit from them.
  
# Installation

* **Windows** - download the installer by clicking the "Windows" button at the top of the page.  Run the installer.

* **Mac** - download the ZIP file by clicking the "Mac" button at the top of the page.  Unzip the file.  Double-click
  to run the program.  Depending on your security settings, you may have to specifically enable this program
  (it's not signed.)
  
* **Linux** - download the tarball by clicking the "Linux" button at the top of the page.  Extract it.  Run the "cytoflow" 
  binary that it contains.

# Documentation

You can find the [developer documentation at ReadTheDocs.](https://cytoflow.readthedocs.io/).  GUI documentation for the currently selected operation or
view appears in the "Help" panel in the GUI.  If you don't see a "Help" 
panel, make sure it's activated by going to the "View" menu and selecting
"Help".

# Example Data

The Jupyter notebooks and screencasts use two example data sets.  
If you'd like to play with them yourself, you can download them here:

* [Basic examples](https://github.com/bpteague/cytoflow/releases/download/{{ site.version }}/cytoflow-{{ site.version }}-examples-basic.zip)
* [Advanced examples](https://github.com/bpteague/cytoflow/releases/download/{{ site.version }}/cytoflow-{{ site.version }}-examples-advanced.zip)

# Help!  I found a bug!

First, are you using the current version?  To check, which version 
you're using, go to the Help menu (Windows) or Cytoflow menu (Mac)
and choose "About Cytoflow...".

You can also try to reproduce the bug in the latest build from git HEAD. 
Those binaries are [on BinTray](https://bintray.com/bpteague/cytoflow/cytoflow#files).

If you have found a bug in the most recent version, you can submit your bug report to the 
[Github issues tracker](https://github.com/bpteague/cytoflow/issues).

# I want to keep up with new Cytoflow releases!

Great! At the [Github page](https://github.com/bpteague/cytoflow/), pull down the "Watch" 
menu and select "Releases only."


# Are there screenshots?

[There are (slightly outdated) screenshots.]({{ site.baseurl }}/screenshots.html)

