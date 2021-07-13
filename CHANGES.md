## Release 1.1 "tdTomato"
Maintenance release.

* Update dependencies to current versions.
* Move CI infrastructure to GitHub Actions.
* Significant re-work of the GUI unit tests

## Release 1.0
Cytoflow's 1.0 release! This marks the state at which Cytoflow is, for all intents and purposes, "feature-complete." Major additions in this release include:

* Update all dependent libraries to their latest versions. Notably, this updates matplotlib to 3.0.2 and PyQt to 5.9.2.
* Overhauled the experimental setup dialog, including the ability to import CSV files with filenames and experimental conditions.
* Packaging differences make program startup much, much faster. Also, a proper Windows installer!

## Release 0.5 "GFP"
* Significant re-work of summary statistics generation and plotting
* Tighten down TASBE calibrated cytometry
* MANY many bug fixes, both in modules and GUI

## Release 0.4.1 
* A GUI for the calibrated cytometry tools!
* Bleedthrough compensation (both linear and piecewise-linear)
* Bead calibration
* Autofluorescence correction
* Color mapping
* Keep the same scales on plots in the same x, y facets
* Significant under-the-hood re-wiring
* Other bug-fixes

## Release 0.3.2
* Fix some Logicle crashers
* Add error bars to barplot, stats views
* Use FastLogicle -- it's faster!

## Release 0.3.0
Public beta!

* The point-and-click GUI is not only functional but useful. Serious restructuring behind the scenes, including a multi-process model to keep the GUI responsive.
* More operations (GMMs) and views (2D histogram, 1 and 2D KDEs, violin plots.)
*Lots (lots) of packaging work. One-click bundles and distribution infrastructure.

## Release 0.2.0
A developer's beta!

* Add a public API to Experiment to add conditions and channels.
* Add scaling options to views, data-driven modules
* Add 1D and 2D gaussian mixture models
* Clean up import mess
* Linear bleedthrough module, quad gate

