---
layout: default
title: {{ site.name }}
---

# Welcome!  New to Cytoflow?  Start with [a screencast.](https://youtu.be/rl1c4SlAfvU)

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

* An emphasis on **metadata**.  CytoFlow assumes that you are measuring
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
  [Jupyter notebook](http://jupyter.org/); in fact, the GUI will export a 
  workflow directly to a notebook!

* **Free and open-source.**  Download the source code from 
  (the GitHub project page)[https://github.com/bpteague/cytoflow] and modify it 
  to suit your own needs, then contribute your changes back so the rest of 
  the community can benefit from them.

## Note: this is still beta software!  Caveat emptor!
  
# Installation

**There isn't any!**  The binaries at the top of the page are all you need.
On a Mac, you'll have to extract the ZIP archive -- then, just double-click
to start the program!

# Documentation

The [developer documentation](https://cytoflow.readthedocs.io/) is quite
complete, but the GUI documentation is lagging.  A good introduction is
[the screencast on Youtube.](https://youtu.be/rl1c4SlAfvU)


# Are there screenshots?

[There are screenshots.]({{ site.baseurl }}/screenshots.html)

