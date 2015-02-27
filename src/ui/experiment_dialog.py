"""
Created on Feb 26, 2015

@author: brian
"""

from traits.etsconfig.api import ETSConfig
from traits.has_traits import HasTraits
ETSConfig.toolkit = 'qt4'

from traits.api import provides, Instance, Str, Int, Property, List, \
                       Constant, Color

from traitsui.api import UI, Group, View, Item, TabularEditor
from traitsui.tabular_adapter import TabularAdapter

from pyface.i_dialog import IDialog
from pyface.api import Dialog

from pyface.qt import QtCore, QtGui
from pyface.qt.QtCore import pyqtSlot

from pyface.api import GUI, FileDialog, DirectoryDialog

import synbio_flowtools as sf

from random import randint, choice, shuffle


#-- Generate 10,000 random single and married people ---------------------------

#-- Person Class Definition ----------------------------------------------------

class Person(HasTraits):

    name    = Str
    address = Str
    age     = Int
    
    # surname is displayed in qt-only row label:
    surname = Property(fget=lambda self: self.name.split()[-1], 
                       depends_on='name')

#-- MarriedPerson Class Definition ---------------------------------------------

class MarriedPerson(Person):

    partner = Instance(Person)

male_names = [ 'Michael', 'Edward', 'Timothy', 'James', 'George', 'Ralph',
    'David', 'Martin', 'Bryce', 'Richard', 'Eric', 'Travis', 'Robert', 'Bryan',
    'Alan', 'Harold', 'John', 'Stephen', 'Gael', 'Frederic', 'Eli', 'Scott',
    'Samuel', 'Alexander', 'Tobias', 'Sven', 'Peter', 'Albert', 'Thomas',
    'Horatio', 'Julius', 'Henry', 'Walter', 'Woodrow', 'Dylan', 'Elmer' ]

female_names = [ 'Leah', 'Jaya', 'Katrina', 'Vibha', 'Diane', 'Lisa', 'Jean',
    'Alice', 'Rebecca', 'Delia', 'Christine', 'Marie', 'Dorothy', 'Ellen',
    'Victoria', 'Elizabeth', 'Margaret', 'Joyce', 'Sally', 'Ethel', 'Esther',
    'Suzanne', 'Monica', 'Hortense', 'Samantha', 'Tabitha', 'Judith', 'Ariel',
    'Helen', 'Mary', 'Jane', 'Janet', 'Jennifer', 'Rita', 'Rena', 'Rianna' ]

all_names = male_names + female_names

male_name   = lambda: choice(male_names)
female_name = lambda: choice(female_names)
any_name    = lambda: choice(all_names)
age         = lambda: randint(15, 72)

family_name = lambda: choice([ 'Jones', 'Smith', 'Thompson', 'Hayes', 'Thomas', 'Boyle',
    "O'Reilly", 'Lebowski', 'Lennon', 'Starr', 'McCartney', 'Harrison',
    'Harrelson', 'Steinbeck', 'Rand', 'Hemingway', 'Zhivago', 'Clemens',
    'Heinlien', 'Farmer', 'Niven', 'Van Vogt', 'Sturbridge', 'Washington',
    'Adams', 'Bush', 'Kennedy', 'Ford', 'Lincoln', 'Jackson', 'Johnson',
    'Eisenhower', 'Truman', 'Roosevelt', 'Wilson', 'Coolidge', 'Mack', 'Moon',
    'Monroe', 'Springsteen', 'Rigby', "O'Neil", 'Philips', 'Clinton',
    'Clapton', 'Santana', 'Midler', 'Flack', 'Conner', 'Bond', 'Seinfeld',
    'Costanza', 'Kramer', 'Falk', 'Moore', 'Cramdon', 'Baird', 'Baer',
    'Spears', 'Simmons', 'Roberts', 'Michaels', 'Stuart', 'Montague',
    'Miller' ])

address = lambda: '%d %s %s' % (randint(11, 999), choice([ 'Spring',
    'Summer', 'Moonlight', 'Winding', 'Windy', 'Whispering', 'Falling',
    'Roaring', 'Hummingbird', 'Mockingbird', 'Bluebird', 'Robin', 'Babbling',
    'Cedar', 'Pine', 'Ash', 'Maple', 'Oak', 'Birch', 'Cherry', 'Blossom',
    'Rosewood', 'Apple', 'Peach', 'Blackberry', 'Strawberry', 'Starlight',
    'Wilderness', 'Dappled', 'Beaver', 'Acorn', 'Pecan', 'Pheasant', 'Owl' ]),
    choice([ 'Way', 'Lane', 'Boulevard', 'Street', 'Drive', 'Circle',
    'Avenue', 'Trail' ]))

people = [ Person(name    = '%s %s' % (any_name(), family_name()),
                   age     = age(),
                   address = address()) for i in range(100) ]

marrieds = [ (MarriedPerson(name    = '%s %s' % (female_name(), last_name),
                              age     = age(),
                              address = address),
               MarriedPerson(name    = '%s %s' % (male_name(), last_name),
                              age     = age(),
                              address = address))
             for last_name, address in
                 [ (family_name(), address()) for i in range(2500) ] ]

for female, male in marrieds:
    female.partner = male
    male.partner   = female
    people.extend([ female, male ])

shuffle(people)

#-- Tabular Editor Definition --------------------------------------------------

#-- Tabular Adapter Definition -------------------------------------------------

class ExperimentSetupAdapter(TabularAdapter):
    """ 
    The tabular adapter interfaces between the tabular editor and the data 
    being displayed. For more details, please refer to the traitsUI user guide. 
    """
    # List of (Column labels, Column ID).
    columns = [ ('Name',    'name'),
                ('Age',     'age'),
                ('Address', 'address')]
                
    '''
    columns = [ ('Name',    'name'),
                ('Age',     'age'),
                ('Address', 'address'),
                ('Spouse',  'spouse') ]
    '''
    row_label_name = 'surname'

    # Interfacing between the model and the view: make some of the cell 
    # attributes a property whose behavior is then controlled by the get 
    # (and optionally set methods). The cell is identified by its column 
    # ID (age, spouse).
    
    # Font fails with wx in OSX; see traitsui issue #13:
    # font                      = 'Courier 10'
    age_alignment             = Constant('right')
    MarriedPerson_age_image   = Property
    MarriedPerson_bg_color    = Color(0xE0E0FF)
    MarriedPerson_spouse_text = Property
    Person_spouse_text        = Constant('')

    def _get_MarriedPerson_age_image(self):
        if self.item.age < 18:
            return '@icons:red_ball'

        return None

    def _get_MarriedPerson_spouse_text(self):
        return self.item.partner.name

# The tabular editor works in conjunction with an adapter class, derived from 
# TabularAdapter. 
tabular_editor = TabularEditor(
    adapter    = ExperimentSetupAdapter(),
    operations = [ 'move', 'edit' ],
    # Row titles are not supported in WX:
    show_row_titles = ETSConfig.toolkit == 'qt4',
)

class ExperimentSetup(HasTraits):
    """
    The model for the TabularEditor in the dialog
    """
    
    people = List(Person)

    view = View(
        Group(
            Item('people', id = 'table', editor = tabular_editor),
            show_labels        = False
        ),
        title     = 'Tabular Editor Demo',
        id        = 'traitsui.demo.Applications.tabular_editor_demo',
        width     = 0.60,
        height    = 0.75,
        resizable = True
    )

@provides(IDialog)
class ExperimentSetupDialog(Dialog):
    """
    Another center pane; this one for setting up an experiment: loading
    FCS files and specifying metadata.  Centered around a table editor.
    """

    id = 'edu.mit.synbio.experiment_setup_dialog'
    name = 'Cytometry Experiment Setup'
    style = 'modal'
    
    experiment = Instance(sf.Experiment)
    model = Instance(ExperimentSetup)
    ui = Instance(UI)
        
    def _create_buttons(self, parent):
        """ 
        Create the buttons at the bottom of the dialog box.
        
        We're overriding (and stealing code from) pyface.qt._create_buttons in
        order to add "Add tube.... " and "Add plate..." buttons.
        """
         
        #buttons = QtGui.QDialogButtonBox()
        buttons = QtGui.QWidget()
        layout = QtGui.QHBoxLayout()
        
        btn_tube = QtGui.QPushButton("Add tube...")
        layout.addWidget(btn_tube)
        QtCore.QObject.connect(btn_tube, QtCore.SIGNAL('clicked()'),
                               self._add_tube)
        
        btn_plate = QtGui.QPushButton("Add plate...")
        layout.addWidget(btn_plate)
        QtCore.QObject.connect(btn_plate, QtCore.SIGNAL('clicked()'),
                               self._add_plate)
        
        layout.addStretch()

        # 'OK' button.
        btn_ok = QtGui.QPushButton("OK")
        btn_ok.setDefault(True)
        layout.addWidget(btn_ok)
        QtCore.QObject.connect(btn_ok, QtCore.SIGNAL('clicked()'),
                               self.control, QtCore.SLOT('accept()'))

        # 'Cancel' button.
        btn_cancel = QtGui.QPushButton("Cancel")
        layout.addWidget(btn_cancel)
        QtCore.QObject.connect(btn_cancel, QtCore.SIGNAL('clicked()'),
                               self.control, QtCore.SLOT('reject()'))   
        
        # add the button container to the widget     
        buttons.setLayout(layout)
        return buttons
    
    def _create_dialog_area(self, parent):
        
        self.model = ExperimentSetup(people = people)
        self.ui = self.model.edit_traits(kind='subpanel', parent=parent)       
        return self.ui.control
    
    def destroy(self):
        self.ui.dispose()
        self.ui = None
        
        super(Dialog, self).destroy()
    
    def _add_tube(self):
        fd = FileDialog()
        fd.wildcard = "*.fcs"
        fd.action = 'open'
        fd.open()
        
        print fd.path
        
    def _add_plate(self):
        print "add plate"
        print type(tabular_editor)
        
        
        c2 = list(tabular_editor.adapter.columns)
        c2.append(('Spouse',  'spouse'))
        tabular_editor.adapter.columns = c2

    
if __name__ == '__main__':

    gui = GUI()
    
    # create a Task and add it to a TaskWindow
    d = ExperimentSetupDialog()
    d.open()
    
    gui.start_event_loop()        