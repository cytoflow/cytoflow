import FlowCytometryTools, copy

class Experiment:
    
    ''' An Experiment is group of FCS measurements with the same channels. The files
    in an experiment should never be changed.
    '''
    
    def __init__(self, files):
        self.files = copy.copy(files)
        self.channel_map = {}
        self.channels = list(self.files[0].channel_names) #stores names to be displayed
        self.ops_performed = []
        self.predecessor = None
        
        #check to see if channels in all the files are the same
        for FCSfile in self.files:
            if len(self.channels) != len(FCSfile.channel_names):
                raise ValueError('different number of parameters')
            else:
                for channel in FCSfile.channel_names:
                    if not channel in self.channels:
                        raise ValueError('different parameters')
        
        for channel in self.channels:
            self.channel_map[channel] = channel
        
    def get_files(self):
        return copy.copy(self.files)
        
    '''make a new experiment with the same settings and history, but with different data
    '''
    def new_updated_exp(self, new_files):
        newexp = Experiment(new_files)
        newexp.predecessor = self
        for operation in self.ops_performed:
            newexp.add_op(operation)
        for channel in self.channels:
            newexp.set_channel_name(self.channel_map[channel], channel)
        return newexp
        
    def get_channels(self):
        return copy.copy(self.channels)
        
    def set_channel_name(self, old_name, new_name):
        index = self.channels.index(old_name)
        self.channels.remove(old_name)
        self.channels.insert(index, new_name)
        self.channel_map[new_name] = self.channel_map[old_name]
        del self.channel_map[old_name]

    def find_orig_channel(self, new_name):
        return self.channel_map[new_name]
        
    def add_op(self, operation):
        self.ops_performed.append(operation)
        
    def get_history(self):
        return copy.copy(self.ops_performed)