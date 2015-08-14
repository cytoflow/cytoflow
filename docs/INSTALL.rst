
* Windows

TO DEVELOP ON THE CODE

Anaconda 2.7 (full install)

from cmd:
 - conda install pandas numexpr seaborn traits pyface envisage pyqt pip
 - pip install FlowCytometryTools
 - install the .exe distributable (from github release)
 - clone the repo using git
 - move or rename the cytoflow, cytoflowgui, and cytoflow-****.egg-info
 - make a file in your site-packages directory named cytoflow.egg-link
   * in the file, put a single line with the directory where you cloned the 
     git repo. eg C:/Users/Kathryn/cytoflow_git/cytoflow
   * 
 - python setup.py develop
 - python run.py


TO JUST RUN THE CODE

 ## PLEASE NOTE, DUE TO A PACKAGING BUG, THIS DOES NOT YET WORK ##

 * Install Anaconda 2.7 (full install)
 * From cmd.exe:
   - conda install pandas numexpr seaborn traits pyface envisage pyqt pip
   - pip install FlowCytometryTools
   - install the .exe distributable (from the github release)
   - search your system for cytoflow.exe
     * it's usually found in C:\Anaconda\Scripts\cytoflow.exe
   - Run it!  Or, drag to the desktop while holding down "control" so 
     as to make a shortcut to it.

