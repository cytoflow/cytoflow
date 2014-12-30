import synbio_model, pandas
import matplotlib
import math
matplotlib.use('TkAgg')
from Tkinter import *
import tkFileDialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

#Opens multple files and puts them in the same experiment.            
def open_files(model, UI):
    model.load_files(tkFileDialog.askopenfilenames())
    channels = model.get_channels(0)
    UI.plot_window.set_axes(channels, 'FSC-A', channels, 'SSC-A')
    UI.plot_window.update_display()
    
class Synbio_UI(Frame):
    
    '''Creates and operates a user interface for the analysis suite.
    '''
    
    def __init__(self, master):
        Frame.__init__(self, master)   
        
        self.parent = master   
        self.model = synbio_model.Synbio_Model() 
        self.plot_window = PlotWindow(self, 300, 300, self.model, (0,0))
        self.initUI()
        
    def initUI(self):

        menubar = Menu(self.parent)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Load FCS file", command=lambda:open_files(self.model, self))
        menubar.add_cascade(label="File", menu=filemenu)
        self.parent.config(menu = menubar)
        
        self.pack()
        
class PlotWindow(Frame):
    
    '''A frame with a plot of an FCS file. Includes dropdown menus to change
    the axes of the plot. Uses matplotlib to plot.
    '''
    
    def __init__(self, master, height, width, model, pop_ID):
        Frame.__init__(self, master)
        self.x_options = []
        self.y_options = []
        self.parent = master
        self.model = model
        self.curr_ID = pop_ID
        f = Figure(figsize=(4,4), dpi=100)
        self.canvas = FigureCanvasTkAgg(f, master=self)
        self.canvas.get_tk_widget().grid(row=0, column=1)
        self.canvas.show()
        self.plot = f.add_subplot(111)
        #self.canvas.pack()
        self.pack()
    
    #creates the dropdown menus for axis selection    
    def set_axes(self, x_params, x_init, y_params, y_init):
        self.x_options = x_params
        self.y_options = y_params
        self.x_current = StringVar(self)
        self.y_current = StringVar(self)
        self.x_current.set(x_init)
        self.y_current.set(y_init)
        self.x_select = OptionMenu(self, self.x_current,*self.x_options, command = lambda x: self.update_display())
        self.x_select.grid(row=1, column=1)
        self.y_select = OptionMenu(self, self.y_current,*self.y_options, command = lambda x: self.update_display())
        self.y_select.grid(row=0, column=0)
    
    #plot the data to the display    
    def update_display(self):
        self.plot.clear()
        self.model.plot_file(self.plot, self.curr_ID[0], self.curr_ID[1], [self.x_current.get(), self.y_current.get()])
        self.canvas.draw()

root = Tk()
root.wm_title("Synthetic biology flow cytometry tools")
ui = Synbio_UI(root)
root.geometry("500x500+300+300")
root.mainloop()