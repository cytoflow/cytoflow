import synbio_model
from Tkinter import *
import tkFileDialog

def donothing():
    pass

class Synbio_UI(Frame):
    
    '''Creates and operates a user interface for the analysis suite.
    '''
    
    def __init__(self, master):
        Frame.__init__(self, master)   
         
        self.parent = master   
        self.model = synbio_model.Synbio_Model() 
        self.initUI()
        
    def initUI(self):
        menubar = Menu(self.parent)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Hello!", command=self.model.load_file(tkFileDialog.askopenfilename()))
        menubar.add_cascade(label="File", menu=filemenu)
        self.parent.config(menu = menubar)

root = Tk()
ui = Synbio_UI(root)

root.mainloop()