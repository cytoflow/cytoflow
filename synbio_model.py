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
        #logtrans = operations.Transform('hlog')
        #exp = logtrans.run_operation(exp)
        self.open_exps.append(exp)
        self.open_files = []
            
    def get_file_names(self):
        return [x.get_ID() for x in self.open_files]
        
    def get_channels(self, exp_num):
        return self.open_exps[exp_num].get_channels()
        
    #creats a plot on the specified canvas. If only one parameter is given,
    #plots a histogram, if 2 are given, plots a dot plot
    def plot_file(self, canvas, exp_num, cell_pop_number, params):
        #canvas.delete("all")
        #canvas_width = canvas.winfo_width()
        #canvas_height = canvas.winfo_height()
        
        pop = self.open_exps[exp_num].get_populations()[cell_pop_number]
        if len(params)==2:
            data = pop.get_data(params)
            
            canvas.plot(data[params[0]], data[params[1]], '.', markersize=0.5)
            #heatmap, xedges, yedges = np.histogram2d(data[params[0]], data[params[1]], bins=500)
            #extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]

            #canvas.imshow(heatmap, extent=extent)
            #maxX = data[params[0]].max()
            #maxY = data[params[1]].max()
            #print maxX, maxY
            #df_iter = data.iterrows()
            #for index, curr_row in df_iter:
                #x_value = canvas_width*curr_row[params[0]]/float(maxX)
                #y_value = canvas_height-canvas_height*curr_row[params[1]]/float(maxY)
                #canvas.create_line(x_value, y_value,x_value+1, y_value, width=1,fill="blue")        
        pop.get_file().plot(params)
        plt.show()
        #return self.open_files[cell_pop_number].get_plot(params)