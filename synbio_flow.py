import FlowCytometryTools, copy
import matplotlib as plt

class Experiment:
    
    ''' An Experiment is group of FCS measurements with the same channels. The files
    in an experiment should never be changed.
    '''
    
    def __init__(self, populations):
        self.populations = populations
        self.population_map = {}
        self.channel_map = {}
        self.channels = list(self.populations[0].channels) #stores names to be displayed
        self.ops_performed = []
        self.predecessor = None
        
        #check to see if channels in all the files are the same
        for FCSfile in self.populations:
            self.population_map[FCSfile.ID] = FCSfile
            if len(self.channels) != len(FCSfile.channels):
                raise ValueError('different number of parameters')
            else:
                for channel in FCSfile.channels:
                    if not channel in self.channels:
                        raise ValueError('different parameters')
        
        for channel in self.channels:
            self.channel_map[channel] = channel
        
    def get_populations(self):
        return copy.copy(self.populations)
        
    '''make a new experiment with the same settings and history, but with different data
    '''
    def new_updated_exp(self, new_populations):
        newexp = Experiment(new_populations)
        newexp.predecessor = self
        for operation in self.ops_performed:
            newexp.add_op(operation)
        for channel in self.channel_map.keys():
            newexp.set_channel_name(self.channel_map[channel], channel)
        return newexp
        
    def get_channels(self):
        return copy.copy(self.channels)
        
    def set_channel_name(self, old_name, new_name):
        if old_name != new_name:
            index = self.channels.index(old_name)
            self.channels.remove(old_name)
            self.channels.insert(index, new_name)
            self.channel_map[new_name] = self.channel_map[old_name]
            del self.channel_map[old_name]

    def find_orig_channels(self, new_names):
        return_names = []
        for name in new_names:
            return_names.append(self.channel_map[name])
        return return_names
        
    def add_op(self, operation):
        self.ops_performed.append(operation)
        
    def get_history(self):
        return copy.copy(self.ops_performed)
        
class CellPopulation:
    
    '''A cell population is a set of cell measurements along with the experimental
    parameters used to generate those cells. A population also stores its gating history.
    Populations are identified by their ID, which is currently the well ID.
    '''
    
    def __init__(self, fcsfile, parameters, gate_list):
        self.fcs = fcsfile
        self.parameters = parameters
        self.channels = fcsfile.channel_names
        self.gate_list = copy.copy(gate_list)
        self.original = fcsfile
        self.ID = fcsfile.get_meta_fields('$FIL')['$FIL']
        
    def new_updated_pop(self, new_file):
        new_pop =CellPopulation(new_file, self.parameters, self.gate_list)
        new_pop.original = self.original
        return new_pop
        
    def get_file(self):
        return self.fcs
        
    def get_gates(self):
        return copy.copy(self.gate_list)
        
    def get_parameter(self, param_name):
        return self.parameters[param_name]
    
    def get_param_names(self):
        return self.parameters.keys()
    
    def set_parameter(self, param_name, param_value):
        self.parameters[param_name] = param_value
    
    def add_gate(self, gate):
        self.gate_list.append(gate)
        
    #returns an matplotlib figure of the population, with the specified parameters.
    #if the second parameter is False, returns a histogram
    def get_plot(self, param1, param2):
        if param2:
            return self.fcs.plot([param1, param2])
        else:
            return self.fcs.plot(param1)