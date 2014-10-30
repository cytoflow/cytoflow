import os, FlowCytometryTools, synbio_flow, pylab
from pylab import *
from synbio_flow import *
from operations import *
from pandas import *
import numpy as np
from scipy.stats import *

datadir = os.path.abspath('synbio-flowtools/test.fcs')
datadir2 = os.path.abspath('synbio-flowtools/test2.fcs')
testSample = FlowCytometryTools.FCMeasurement(ID= "testsample", datafile = datadir)
testSample2 = FlowCytometryTools.FCMeasurement(ID= "testsample2", datafile = datadir2)

figure();
plot1 = testSample.plot(['FSC-A', 'EYFP-A'], kind='scatter')

expTest = Experiment([CellPopulation(testSample, {},[]), CellPopulation(testSample2, {},[])])
#print expTest.get_channels()
expTest.set_channel_name('EYFP-A', 'yellow')
#print expTest.get_channels()
logtrans = Transform('hlog')
logtrans.set_parameter('channels', ['yellow', 'mKate-A'])
newexp = logtrans.run_operation(expTest)
#print newexp.get_channels()
median = Statistics('median')
median.set_parameter('channels', ['yellow', 'mKate-A'])
#print testSample.meta.keys()
#print gmean([1,2,2])
print median.run_operation(expTest)


figure();
newexp.get_populations()[0].get_file().plot(['EYFP-A', 'mKate-A'], kind='scatter')

'''
figure();
newexp.get_files()[1].plot(['EYFP-A', 'mKate-A'], kind='scatter')
'''
gate = GateAll(FlowCytometryTools.ThresholdGate(200000.0, 'mKate-A', 'above'), 'above m_kate')
gated = gate.run_operation(expTest)

figure();
gated.get_populations()[0].get_file().plot(['EYFP-A', 'mKate-A'], kind='scatter')
print gated.get_populations()[0].gate_list

plt.show()