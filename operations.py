import FlowCytometryTools
import numpy as np
from pandas import *
from synbio_flow import Experiment

class Operation:
    
    '''An Operation represents a function to be performed on an experiment.
    An operation is run by calling the run_operation method.
    The data and history of the input experiment should remain the same after
    an operation is performed. Any outputs (experiments, numerical data, etc) will
    be returned by the run_operation method.
    '''
    
    def __init__(self):
        self.parameters = {}
    
    # if the return type is new FCS data, return a new Experiment, with same
    # settings but new data. Will never mutate the previous experiment.
    def run_operation(self, experiment):
        raise NotImplementedError
    
    def get_parameters_needed(self):
        return self.parameters.keys()
        
    def set_parameter(self, param_name, param_value):
        if not param_name in self.parameters.keys():
            raise ValueError('parameter not appropriate for operation')
        else:
            self.parameters[param_name] = param_value
        
class Transform(Operation):
    
    '''Returns a new experiment with the specified transformation applied to the
    original data. Currently supported transformations are base_10 hyperlog ('hlog'),
    base_10 truncated log ('tlog') and linear scaling. If no channels are specified
    the transformation is applied to all channels.
    '''
    
    def __init__(self, trans_type):
        Operation.__init__(self)
        self.trans_type = trans_type
        self.parameters['direction'] = 'forward'
        self.parameters['channels'] = None
    
    def run_operation(self, experiment):
        channel_corr_names = experiment.find_orig_channels(self.parameters['channels'])
        new_files = []
        for fcs in experiment.get_files():
            new_files.append(fcs.transform(self.trans_type, \
            channels = channel_corr_names))
        result = experiment.new_updated_exp(new_files)
        result.add_op(self)
        return result
        
class Statistics(Operation):
    
    '''Returns a data table of the specified statistic applied to the experiment
    data on the specified channels. If no channels are specified, computes and
    returns the statistic for all channels.
    '''
    
    def __init__(self, stats_type):
        Operation.__init__(self)
        self.stats_type = stats_type
        self.parameters['channels'] = None
        
    def run_operation(self, experiment):
        channel_corr_names = experiment.find_orig_channels(self.parameters['channels'])
        data = DataFrame(columns = channel_corr_names)
        for fcs in experiment.get_files():
            new_data = fcs.data[channel_corr_names].median(axis = 0).transpose();
            #new_data = DataFrame(data = [fcs.ID_from_data]).append(new_data, ignore_index = True)
            data = concat([data, new_data])
        return data