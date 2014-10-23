import os, FlowCytometryTools, synbio_flow, pylab
from pylab import *
from synbio_flow import *
from operations import *
from pandas import *
import numpy as np

datadir = os.path.abspath('synbio-flowtools/test.fcs')
datadir2 = os.path.abspath('synbio-flowtools/test2.fcs')
testSample = FlowCytometryTools.FCMeasurement(ID= "testsample", datafile = datadir)
testSample2 = FlowCytometryTools.FCMeasurement(ID= "testsample2", datafile = datadir2)

#figure();
#plot1 = testSample.plot(['EYFP-A', 'mKate-A'], kind='scatter')

expTest = Experiment([testSample, testSample2])
#print expTest.get_channels()
expTest.set_channel_name('EYFP-A', 'yellow')
#print expTest.get_channels()
logtrans = Transform('hlog')
logtrans.set_parameter('channels', ['yellow', 'mKate-A'])
newexp = logtrans.run_operation(expTest)
#print newexp.get_channels()
median = Statistics('median')
median.set_parameter('channels', ['yellow', 'mKate-A'])
print median.run_operation(newexp)
print np.array([1,2])
print testSample.data[['EYFP-A', 'mKate-A']].median(axis = 0).T

'''
figure();
newexp.get_files()[0].plot(['EYFP-A', 'mKate-A'], kind='scatter')
figure();
newexp.get_files()[1].plot(['EYFP-A', 'mKate-A'], kind='scatter')
'''

plt.show()