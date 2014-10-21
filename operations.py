import FlowCytometryTools
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
    
    #return a new Experiment, with same settings but new data
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
    
    def __init__(self, trans_type):
        Operation.__init__(self)
        self.parameters['trans_type'] = trans_type
        self.parameters['direction'] = 'forward'
        self.parameters['channels'] = None
    
    def run_operation(self, experiment):
        channel_corr_names = []
        for channel in self.parameters['channels']:
            channel_corr_names.append(experiment.find_orig_channel(channel))
        new_files = []
        for fcs in experiment.get_files():
            new_files.append(fcs.transform(self.parameters['trans_type'], \
            channels = channel_corr_names))
        result = experiment.new_updated_exp(new_files)
        result.add_op(self)
        return result