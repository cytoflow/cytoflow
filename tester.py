import os, FlowCytometryTools, synbio_flow, pylab
from pylab import *
from synbio_flow import *
from operations import *

datadir = os.path.abspath('synbio-flowtools/test.fcs')
testSample = FlowCytometryTools.FCMeasurement(ID= "testsample", datafile = datadir)

#figure();
#plot1 = testSample.plot(['EYFP-A', 'mKate-A'], kind='scatter')

expTest = Experiment([testSample])
print expTest.get_channels()
expTest.set_channel_name('EYFP-A', 'yellow')
print expTest.get_channels()
logtrans = Transform('hlog')
logtrans.set_parameter('channels', ['yellow', 'mKate-A'])
newexp = logtrans.run_operation(expTest)
figure();
newexp.get_files()[0].plot(['EYFP-A', 'mKate-A'], kind='scatter')

transformed = testSample.transform('hlog', channels=['EYFP-A', 'mKate-A'])
figure();
transformed.plot(['EYFP-A', 'mKate-A'], kind='scatter')

plt.show()