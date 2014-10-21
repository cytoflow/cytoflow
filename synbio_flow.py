import FlowCytometryTools, copy

class Experiment:
    
    def __init__(self, files):
        self.files = copy.copy(files)
        self.channel_map = {}
        self.channels = self.files[0].channel_names
        self.ops_performed = []
        
        #check to see if channels in all the files are the same
        for FCSfile in self.files:
            if len(self.channels) != len(FCSfile.channel_names):
                raise ValueError('different number of parameters')
            else:
                for channel in self.channels:
                    if not any(channel in FCSfile.channel_names):
                        raise ValueError('different parameters')
        
    def get_files(self):
        return copy.copy(self.files)
        
    def replace_files(self, newFiles):
        self.files = copy.copy(newFiles) 
        
    def get_channels(self):
        return self.channels
        
    def set_channel_name(self, old_name, new_name):
        self.channelMap[new_name] = old_name

    def find_orig_channel(self, new_name):
        return self.channelMap[new_name]
        
    def add_op(self, operation):
        self.ops_performed.append(operation)