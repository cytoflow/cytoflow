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
from operations.hlog import HlogTransformOp
from operations.import_op import ImportOp
from views.histogram import HistogramView
from views.range_selection import RangeSelection
from views.threshold_selection import ThresholdSelection

try:
    from operations.logicle import LogicleTransformOp
except ImportError:
    pass
