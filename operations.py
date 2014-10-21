import FlowCytometryTools
from synbio_flow import Experiment

class Operation:
    
    def __init__(self):
        self.parameters = {}
    
    def run_operation(self, experiment):
        raise NotImplementedError
    
    def get_parameters_needed(self):
        return self.parameters.keys()
        
    def set_parameter(self, param_name, param_value):
        if not self.parameters.keys().contains(param_name):
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
        new_files = []
        for fcs in experiment.get_files():
            new_files.append(fcs.transform(self.parameters['trans_type'], \
            channels = self.parameters['channels']))
        experiment.replace_files(new_files)
        experiment.add_op(self)