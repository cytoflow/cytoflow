.. _user_computational:

Tutorial: Computational Cytometry
=================================

*Cytoflow* includes modules and views for analyzing and visualizing 
high-dimensional data from flow cytometry experiments. Often called 
**computational cytometry,** these semi-supervised and unsupervised analysis 
pipelines are generally broken into three major pieces:

1. *Clean and pre-process the data.* Check for tubes that have artifacts / 
   discontinuities in the flow rate, for example, and then compensate for 
   spill-over between channels. Possibly warp the channels between tubes to 
   bring peaks into registration. Because these data are pre-processed, those 
   capabilities are not demonstrated here, but see the **Bleedthrough Compensation**,
   **FlowClean** and **Registration** operations details on how to perform these
   cleaning steps.
   
   .. attention:: 
      Often, pre-processing also involves scaling data with a logarithmic or 
      biexponential transformation. However, *Cytoflow* maintains the underlying
      data in its unscaled form, and scales it as needed for processing or 
      visualization.
      
2. *Cluster or reduce the dimensionality of the data.* Cytoflow includes several
   clustering algorithms -- *KMeans*, *FlowPeaks*, and *self-organizing maps* -- 
   and two dimensionality reduction methods, *principle components analysis* and
   t*-distributed stochastic neighbor embedding.* Self-organizing maps and tSNE 
   are demonstrated below.

3. *Visualize the data to explore the biology.* For dimensionality-reduction 
   methods like tSNE and PCA, standard scatterplots are used. However, for 
   high-dimensional clustering, a **minimum-spanning tree** has become common. 
   *Cytoflow* allows a user to create both visualizations, and each is 
   demonstrated below as well.

This notebook demonstrates self-organized maps (SOM), minimum-spanning trees, 
and t-distributed stochastic neighbor embedding (t-SNE) using data from 
*Saeys Y, Van Gassen S, Lambrecht BN. Computational flow cytometry: helping to* 
*make sense of high-dimensional immunology data. Nature Reviews Immunology* 
*16:449-462 (2016).* The workflow below reproduces many of the figures from that
paper. (It's a great paper -- go read it!)

The example data files are taken from :ref:`the hierarchical gating tutorial <user_hierarchical>`, 
which applied manual gating to identify NK, NK T, T and B cells; neutrophils, DCs, 
basophils, and macrophages. After running the operations in that workflow, I 
used the *Export FCS* operation to export each different cell type in a 
different .FCS file. These manual gates serve as the "ground truth" to evaluate 
the performance of the clustering, dimensionality reduction, and visualization 
algorithms.

If you'd like to follow along, you can do so by downloading one of the
**cytoflow-#####-examples-advanced.zip** files from the 
`Cytoflow releases page <https://github.com/cytoflow/cytoflow/releases>`_
on GitHub. These example files are in the *saeys/* sub-folder.

One final note. **I am not an immunologist.** This is an explanatory example,
using publically available data, to illustrate the software's functionality.
*Please* don't write me and tell me I'm using the wrong markers or the
wrong dyes.

Import the data
---------------

Open the experiment setup panel and set it up as in the image below. We will
include just one piece of per-tube metadata, the cell type from the 
:ref:`hierarchical gating example. <user_hierarchical>`

.. image:: images/computational01.png

There are about 230,000 events across the 8 samples, so this is not a toy
data set! Let's remove unused channels (FITC, AmCyan, Pacific Blue) and the 
SSC channels, then rename the remaining ones to track their markers.

.. image:: images/computational02.png

Click *Import* to import the data.


Gate for single, live cells
---------------------------

The exported FCS files were not pre-gated to remove debris and clumps. Instead 
of using a manual gate, let's use a *Density Gate* gate on ``FSC_H`` and ``FSC_W``
to select 80% of the events in the densest clusters. It's more reproducible and 
less biased than manual gating!

.. image:: images/computational03.png

Of course, I say that, then turn around to draw a manual *Range Gate* on the
``Live_Dead`` channel. This one is pretty obvious, though. Remember, the **live**
cells are the ones that **don't** stain.

.. image:: images/computational04.png

Clustering with self-organizing maps
------------------------------------

SOMs use a grid of interconnected "neurons" to that are trained to categorize 
high-dimensional inputs. For a reasonable panel like the 9-marker panel we're 
using, the default settings seem to be fine, but there are a lot of other 
parameters that can be tweaked. See the **Self Organizing Map** module 
documentation for details. I also highly suggest reading 
`this introduction <https://rubikscode.net/2018/08/20/introduction-to-self-organizing-maps/>`_ and 
`this tutorial <https://www.datacamp.com/tutorial/self-organizing-maps>`_ -- the *Tuning the* 
*SOM Model* section in that second link is particularly helpful!

We use *Self-Organizing Map* operation just like any other data-driven 
operation --add the operation, set the parameters, and click *Estimate*. This 
one can take a minute or so on a decent computer, so be patient. This algorithm 
also works substantially better on scaled data, so we'll scale each channel with
the *logicle* biexponential scale before training the map.

.. image:: images/computational05.png

In this example, we know the ground truth, but in general we won't -- so we need
to use internal measures to evaluate the performance of our classifier. In this 
case, default view is a diagnostic view so we can get a sense of how well the 
training went. The top plot is a distance map, where each cell represents one 
neuron and the color represents how close the neuron is to its adjacent neurons. 
Think of it as a topographic map where the input data will cluster in the 
"valleys". In this case, we can see that there is a "ridge" between two major 
"valleys" -- we'll see later if those correspond to any major cell types.

The other plot that the diagnostic view gives you is a plot of the quantization 
error over the training epochs. Lower quantization error means the model fits 
the data better. This should decrease, but it pretty much always looks asymptotic. 
If it doesn't seem to have decreased much, increase the number of iterations, 
but beware -- later iterations give you less of a decrease each time than 
earlier ones!

To use *Cytoflow*'s self-organizing map module effectively, it's important to
understand what it did. First, as we can see in the *Experiment Browser*, it 
added a statistic with the same name as the operation. Each row is a cluster and 
each column is one of the channels the model was trained on. The data in the 
statistic is the **center** of each cluster, which is used later for plotting
the results.

.. image:: images/computational06.png

The other thing the *Self Organizing Map* module does is create a new condition
in the experiment, also named the same as the operation. This condition 
classifies each event as a member of one of the clusters -- we can see this
in the *Experiment Browser* as well.

.. image:: images/computational07.png

As we can see in the *Experiment Browser*, SOM only gave us three clusters --
and there are definitely more cell types than that! Let's see how each cluster
is composed of the cell types. First, we'll make a *Channel Statistic* and
count events, broken out by *SOM_Cluster* and *Cell_type* and subsetted by
both *Live+* and *Single_Cell+*. (Since we're counting, the channel doesn't
matter! I've set it to *FSC_A*.)

.. image:: images/computational08.png

Let's make some pie plots. The two views that can do that are *Matrix View*
and *Minimum Spanning Tree* -- *Matrix View* is easier to set up, so let's use
that.

.. image:: images/computational09.png

Well. We got three clusters -- one is mostly B cells, one is mostly T cells 
(with some NK and NK T cells), and one is "everything else" -- DCs, macrophages, 
basophils, neutrohpils. The reason we ended up with only three clusters here is 
because most of the cells in the data set are B and T cells!

Can we do better? By default, the *Cytoflow*'s self organizing maps module
uses consensus clustering to find the "natural" number of clusters -- but 
sometimes we want more resolution. Remember that each neuron in the 
self-organizing map actually defines a cluster, so the "natural" clusters are 
actually clusters of clusters!

You can disable the consensus clustering by un-checking the *Consensus Cluster* 
option. You'll need to re-estimate the SOM, but everything else should recompute
automatically.

.. image:: images/computational10.png

The matrix view is a little hard to interpret, though. There are definitely more
distinct clusters, but it's not clear how (or if) those clusters relate to
eachother.

.. image:: images/computational11.png

Remember how the SOM operation adds a statistic with the location of the center
of each cluster? We can use this to our advantage, laying out the pie graphs
with a *Minimum Spanning Tree* view.

.. image:: images/computational12.png

Much better! We can see that, while most of the clusters are (as expected)
T and B cells, the DCs, NKs, NK Ts, and neutrophils have each (mostly) clustered
with eachother. The macrophages and the basophils are in a single cluster --
perhaps even more clusters would have distinguished them. 

.. note::
   If you would like, you can scale each pie plot by the number of events in 
   that cluster, using the appropriate option to the *Minimum Spanning Tree* view.
   
Remember, though, that here we have the ground truth in this data set, and 
usually you won't. Let's use the same tree to plot different data -- in this 
case, the **geometric mean** of each of the 9 marker channels.

First, we need to create a new statistic. We'll use the *Multi Channel Statistic*
to break the data set apart by different values of the *SOM_Cluster* condition,
then compute the geometric mean for each channel in each subset.

.. image:: images/computational13.png

Now we'll plot a minimum-spanning tree with the same cluster **locations** but
using the statistic we just created for the **data**. The key to using the
minimum spanning tree view this way is to **leave the variable and features blank**
-- we want to plot the "whole" statistic, not just part of it. (When used this 
way, the MST and matrix views treat the **features** as the variables.)

.. image:: images/computational14.png

Now we can see that the fairly obvious classes of cells and their marker levels. 
High CD19 (and mostly low owther things) are B cells; high CD3 (and mostly low 
other things) are T cells. But there are a few clusters that are different, 
and those correspond to the other cell types.

t-distributed Stochastic Neighbor Embedding
-------------------------------------------

Self-organizing maps (and other clustering algorithms like K-means and 
FlowPeaks) are **classifiers** -- they take points in a high-dimensional space 
and sort them into bins based on a how close they are to eachother. These 
algorithms consider all of the dimensions -- in this case, all 9 of the 
channels -- but they are subject to the **curse of dimensionality** where 
increased numbers of dimensions make distance-based algorithms begin to fail.

Another approach is to reduce the number of dimensions, **embedding** the original
high-dimensional data set into a lower-dimensional (usually 2) space. The trick 
is to do so in a way that retains the structure, keeping "close" observations 
in the higher-dimensional space still "close" in the lower-dimensional embedding.

*t-distributed Stochastic Neighbor Embedding* is an algorithm that promises to 
do just that. It is one of many non-linear dimensionality reduction methods -- 
its benefit over linear dimensionality reductions such as principal components 
analysis (PCA) is that is more faithfully maintains local structure.

This comes with a cost, of course, and that cost is computational complexity! 
On this fairly modest data set, computing the embedding takes over four minutes to 
run. So be patient! The results are worth it, I promise. The *tSNE* module prints
updates as it runs so you won't think it's crashed.

Also, the tSNE algorithm can also peform better or worse using different ways 
of measuring "distance" in the original high-dimensional space. For two or three
channels, ``euclidean`` is fine, but for higher numbers of channels ``cosine`` seems 
to work better. Finally, this performs *much* better on scaled data, so we're 
using ``logicle`` scale for all of the channels. Just as with self-organizing
maps, there are a number of parameters that can change the performance of the 
algorithm. Read the operation documentation for details.

As with self-organizing maps, we add a *tSNE* operation and tell it what channels
and scales to use.

.. image:: images/computational15.png

Note that the *tSNE* operation has added two synthetic "channels" to the 
experiment - *t_SNE1* and *tSNE_2*. (These will change if you change the
name of the operation.)

.. image:: images/computational16.png

If we plot them on a scatter plot and color by cell type, we see that the
different types mostly cluster together!

.. image:: images/computational17.png

Again, we usually won't have the ground truth -- so it's again good to evaluate 
the clusters by plotting the relative amounts of each marker in each cluster. 
The following graphs do so by setting the *Color Channel* and *Color Scale* 
attributes of the scatter plot, which relate the color of each event to the 
(scaled) value of a channel. I've also used different palettes, just to show
off the various visual style options.

.. image:: images/computational18.png

.. image:: images/computational19.png

.. image:: images/computational20.png

.. image:: images/computational21.png

.. image:: images/computational22.png

.. image:: images/computational23.png

.. image:: images/computational24.png

.. image:: images/computational25.png

.. image:: images/computational26.png




