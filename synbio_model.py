import synbio_flow, operations
from pylab import *
import numpy as np

class Synbio_Model:
    
    '''Handles requests from the user interface, and returns the appropriate 
    plots and options to the user interface.
    '''
    
    def __init__(self):
        self.open_exps = []
        self.open_files = []
        
    #makes a new CellPopulation from the file specified by filename.
    #throws an IOError if the file cannot be parsed into a CellPopulation
    def load_files(self, filenames):
        for filename in filenames:
            fcsfile = synbio_flow.load_file(filename, filename)
            self.open_files.append(fcsfile)
        exp = synbio_flow.Experiment(self.open_files)
        self.open_exps.append(exp)
        self.open_files = []
            
    def get_file_names(self):
        return [x.get_ID() for x in self.open_files]
        
    def get_channels(self, exp_num):
        return self.open_exps[exp_num].get_channels()
        
    #creats a plot on the specified canvas. If only one parameter is given,
    #plots a histogram, if 2 are given, plots a dot plot
    def plot_file(self, canvas, exp_num, cell_pop_number, params):
        
        pop = self.open_exps[exp_num].get_populations()[cell_pop_number]
        if len(params)==2:
            data = pop.get_data(params)
            canvas.plot(data[params[0]], data[params[1]], '.', markersize=0.5)
      
        pop.get_file().plot(params)
        plt.show()