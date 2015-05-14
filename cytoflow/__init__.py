# make sure pandas is new enough
from pandas.version import version as _pd_version
from distutils.version import LooseVersion

if LooseVersion(_pd_version) < '0.15.0':
    raise ImportError('cytoflow needs pandas >= 0.15.0.  trust me.')

# make sure numexpr is around.

from numexpr import version as _numexpr_version

if LooseVersion(_numexpr_version.version) < '2.1':
    raise ImportError('cytoflow needs numexpr >= 2.1')

from experiment import Experiment
from operations.threshold import ThresholdOp
from operations.range import RangeOp
from operations.range2d import Range2DOp
from operations.hlog import HlogTransformOp
from operations.import_op import ImportOp, Tube
from views.histogram import HistogramView
from views.hexbin import HexbinView
from views.scatterplot import ScatterplotView
from views.range_selection import RangeSelection
from views.range_selection_2d import RangeSelection2D
from views.threshold_selection import ThresholdSelection

try:
    from operations.logicle import LogicleTransformOp
except ImportError:
    pass

__version__ = "0.1.3"
