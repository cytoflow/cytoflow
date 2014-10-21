import os, FlowCytometryTools, synbio_flow, pylab
from pylab import *
from synbio_flow import *
from operations import *

datadir = os.path.abspath('synbio-flowtools/test.fcs')
testSample = FlowCytometryTools.FCMeasurement(ID= "testsample", datafile = datadir)

#figure();
#plot1 = testSample.plot(['EYFP-A', 'mKate-A'], kind='scatter')

expTest = Experiment([testSample])
#print expTest.getFiles()
logtrans = Transform('hlog')
logtrans.run_operation(expTest)
figure();
expTest.get_files()[0].plot(['EYFP-A', 'mKate-A'], kind='scatter')

transformed = testSample.transform('hlog', channels=['EYFP-A', 'mKate-A'])
figure();
transformed.plot(['EYFP-A', 'mKate-A'], kind='scatter')

plt.show()