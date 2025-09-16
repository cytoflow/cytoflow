.. _user_reference:

**************************
Operation and View Gallery
**************************

Below is a gallery of *Cytoflow*'s operations and views. Each header will take
you to the corresponding manual page.

Operations
==========

Gates
-----

.. grid:: 2 3 3 3 
	
	.. grid-item-card:: Threshold Gate
		:img-top: /operations/threshold-1.png
		:link: operations/threshold
		:link-type: doc
	
	.. grid-item-card:: Range Gate
		:img-top: /operations/range-1.png
		:link: operations/range
		:link-type: doc
	
	.. grid-item-card:: Quad Gate
		:img-top: /operations/quad-1.png
		:link: operations/quad
		:link-type: doc
	
	.. grid-item-card:: Rectangle Gate
		:img-top: /operations/range2d-1.png
		:link: operations/range2d
		:link-type: doc
	
	.. grid-item-card:: Polygon Gate
		:img-top: /operations/polygon-1.png
		:link: operations/polygon
		:link-type: doc
	
	.. grid-item-card:: Gate Hierarchy
	
	.. grid-item-card:: Gate Categories
	

Statistics and Transforms
-------------------------

.. grid:: 2 3 3 3 

	.. grid-item-card:: Channel Statistic
	
	.. grid-item-card:: Multi-Channel Statistic
	
	.. grid-item-card:: Transform Statistic
	
	.. grid-item-card:: Ratio
	
	
Preprocessing
-------------

.. grid:: 2 3 3 3 

	.. grid-item-card:: Linear Bleedthrough Compensation
		:img-top: /operations/bleedthrough_linear-1.png
		:link: operations/bleedthrough_linear
		:link-type: doc
	
	.. grid-item-card:: FlowClean
		:img-top: /operations/flowclean-1.png
		:link: operations/flowclean
		:link-type: doc
	
	.. grid-item-card:: Peak Registration
	
	.. grid-item-card:: Autofluorescence Correction
		:img-top: /operations/autofluorescence-1.png
		:link: operations/autofluorescence
		:link-type: doc
	
	.. grid-item-card:: Bead Calibration
		:img-top: /operations/bead_calibration-1.png
		:link: operations/bead_calibration
		:link-type: doc
	
	.. grid-item-card:: Color Translation
		:img-top: /operations/color_translation-1.png
		:link: operations/color_translation
		:link-type: doc
	
	.. grid-item-card:: TASBE
		:img-top: /operations/tasbe-4.png
		:link: operations/tasbe
		:link-type: doc
	
	
Clustering
----------

.. grid:: 2 3 3 3 

	.. grid-item-card:: Binning
		:img-top: /operations/binning-1.png
		:link: operations/binning
		:link-type: doc
	
	.. grid-item-card:: Density Gate
		:img-top: /operations/density-1.png
		:link: operations/density
		:link-type: doc
	
	.. grid-item-card:: One Dimensional Gaussian Mixtures
		:img-top: /operations/gaussian_1d-1.png
		:link: operations/gaussian_1d
		:link-type: doc
	
	.. grid-item-card:: Two Dimensional Gaussian Mixtures
		:img-top: /operations/gaussian_2d-1.png
		:link: operations/gaussian_2d
		:link-type: doc
	
	.. grid-item-card:: K-Means Clustering
		:img-top: /operations/kmeans-1.png
		:link: operations/kmeans
		:link-type: doc
	
	.. grid-item-card:: FlowPeaks
		:img-top: /operations/flowpeaks-1_01.png
		:link: operations/threshold
		:link-type: doc
	
	.. grid-item-card:: Self-organizing maps (SOM)
	
	.. grid-item-card:: Minimum Spanning Tree
	

Dimensionality Reduction
------------------------

.. grid:: 2 3 3 3 

	.. grid-item-card:: Principal Components Analysis (PCA)
	
	.. grid-item-card:: t-Distributed Stochastic Neighborhood Embedding (tSNE)
		:img-top: /operations/tsne-1.png
		:link: operations/tsne
		:link-type: doc
	
	
Views
=====

One Dimensional
---------------

.. grid:: 2 3 3 3 

	.. grid-item-card:: Histogram
		
	.. grid-item-card:: One-dimensional KDE
	
	.. grid-item-card:: Violin Plot
	
Two Dimensional
---------------

.. grid:: 2 3 3 3 

	.. grid-item-card:: Scatterplot
	
	.. grid-item-card:: Density Plot
	
	.. grid-item-card:: Two-dimensional histogram
	
	.. grid-item-card:: Two-dimensional KDE
	

Multi-Dimensional
-----------------

.. grid:: 2 3 3 3 

	.. grid-item-card:: Parallel Coordinates Plot
	
	.. grid-item-card:: Radviz
	

Statistics
----------

.. grid:: 2 3 3 3 

	.. grid-item-card:: Bar Chart
	
	.. grid-item-card:: 1D Statistics Plot
	
	.. grid-item-card:: 2D Statistics Plot
	
	.. grid-item-card:: Matrix View
	
	.. grid-item-card:: Minimum Spanning Tree
	
	
Miscellaneous
-------------

.. grid:: 2 3 3 3 

	.. grid-item-card:: Table View
	
	.. grid-item-card:: Long Table View
	
	.. grid-item-card:: FCS Export
	
	


.. list-table::

       
       
   * - :doc:`Channel Statistics <operations/channel_stat>`
       
     - :doc:`Principle Component Analysis <operations/pca>`
       
   * - :doc:`Ratio <operations/ratio>`
       
     - :doc:`Transform Statistic <operations/xform_stat>`

   
Views
=====
   
.. list-table::

   * - :doc:`Bar Chart <views/bar_chart>`
   
       .. figure:: /views/bar_chart-1.png
       
     - :doc:`Density Map <views/density>`
   
       .. figure:: /views/density-1.png
       
     - :doc:`Export FCS <views/export_fcs>`
          
     - :doc:`Histogram <views/histogram>`
   
       .. figure:: /views/histogram-1.png
       
   * - :doc:`2D Histogram <views/histogram_2d>`
   
       .. figure:: /views/histogram_2d-1.png
          
     - :doc:`Kernel Density Estimate <views/kde_1d>`
   
       .. figure:: /views/kde_1d-1.png
       
     - :doc:`2D Kernel Density Estimate <views/kde_2d>`
   
       .. figure:: /views/kde_2d-1.png
       
     - :doc:`Parallel Coordinates Plot <views/parallel_coords>`
   
       .. figure:: /views/parallel_coords-1.png
       
   * - :doc:`RadViz Plot <views/radviz>`
   
       .. figure:: /views/radviz-1.png
          
     - :doc:`Scatterplot <views/scatterplot>`
   
       .. figure:: /views/scatterplot-1.png
       
     - :doc:`1D Statistics Plot <views/stats_1d>`
   
       .. figure:: /views/stats_1d-1.png
       
     - :doc:`2D Statistics Plot <views/stats_2d>`
   
       .. figure:: /views/stats_2d-1.png
   
   * - :doc:`Table View <views/table>`
   
       .. figure:: /views/table-1.png
       
     - :doc:`Long Table View <views/long_table>`
     
       .. figure:: /views/long_table-1.png
          
     - :doc:`Violin Plot <views/violin>`
   
       .. figure:: /views/violin-1.png
       
     -

  
Operations
----------

.. toctree::
   :glob:

   operations/*
   
   
Views
-----
   
.. toctree::
   :glob:
   
   views/*
   