#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup, find_packages, Extension
import io, os

import versioneer
    
no_logicle = os.environ.get('NO_LOGICLE', None) == 'True'

here = os.path.abspath(os.path.dirname(__file__))

def read_rst(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read_rst('README.rst')

# sphinx is only required for building packages, not for end-users
try:
    from sphinx.setup_command import BuildDoc
    cmdclass = versioneer.get_cmdclass({'build_sphinx' : BuildDoc})
except ImportError:
    cmdclass = versioneer.get_cmdclass()
        
setup(
    name = "cytoflow",
    version = versioneer.get_version(),  # @UndefinedVariable
    packages = find_packages(exclude = ["package", "package.qt"]),
    cmdclass = cmdclass,
    
    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['numpy==1.20.2',
                        'pandas==1.2.5',
                        'matplotlib==3.3.4',
                        'bottleneck==1.3.2',
                        'numexpr==2.7.3',
                        'scipy==1.6.2',
                        'scikit-learn==0.24.2',
                        'seaborn==0.11.1',
                        'statsmodels==0.12.2',
                        'natsort==7.1.1',
                        
                        'traits==6.2.0',
                        'traitsui==7.1.1',
                        'pyface==7.3.0',
                        'envisage==6.0.1',
                        'nbformat==5.1.3',
                        'python-dateutil==2.8.1',
                        'importlib_resources==5.2.0',

                        
                        # pyqt, qt are not in pip
                        # need to install through your package manager
                        'pyopengl==3.1.1a1', 

                        'camel==0.1.2',
                        'yapf==0.30.0',
                        'fcsparser==0.2.1'],
                            
    # GUI also requires PyQt4 >= 5.9.2, but it's not available via pypi and 
    # distutils.  Install it locally!
                        
    # try to build the Logicle extension
    ext_modules = [Extension("cytoflow.utility.logicle_ext._Logicle",
                             sources = ["cytoflow/utility/logicle_ext/FastLogicle.cpp",
                                        "cytoflow/utility/logicle_ext/Logicle.cpp",
                                        "cytoflow/utility/logicle_ext/Logicle.i"],
                             depends = ["cytoflow/utility/logicle_ext/FastLogicle.cpp",
                                        "cytoflow/utility/logicle_ext/Logicle.cpp",
                                        "cytoflow/utility/logicle_ext/Logicle.i",
                                        "cytoflow/utility/logicle_ext/logicle.h"],
                             swig_opts=['-c++', '-py3'])] \
                if not no_logicle else None,
    
    package_data = { 'cytoflowgui' : ['preferences.ini',
                                      'images/*',
                                      'op_plugins/images/*',
                                      'view_plugins/images/*',
                                      'help/*.html',
                                      'help/_images/*.png',
                                      'help/_static/*']},

    # metadata for upload to PyPI
    author = "Brian Teague",
    author_email = "bpteague@gmail.edu",
    description = "Python tools for quantitative, reproducible flow cytometry analysis",
    long_description = long_description,
    license = "GPLv2",
    keywords = "flow cytometry scipy",
    url = "https://github.com/cytoflow/cytoflow", 
    classifiers=[
                 'Development Status :: 5 - Production/Stable',
                 'Environment :: Console',
                 'Environment :: MacOS X',
                 'Environment :: Win32 (MS Windows)',
                 'Environment :: X11 Applications :: Qt',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
                 'Natural Language :: English',
                 'Operating System :: MacOS',
                 'Operating System :: Microsoft :: Windows',
                 'Operating System :: POSIX :: Linux',
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: 3.5',
                 'Programming Language :: Python :: 3.6',
                 'Programming Language :: Python :: 3.7',
                 'Programming Language :: Python :: Implementation :: CPython',
                 'Topic :: Scientific/Engineering :: Bio-Informatics',
                 'Topic :: Software Development :: Libraries :: Python Modules'],
    
    entry_points={'console_scripts' : ['cf-channel_voltages = cytoflow.scripts.channel_voltages:main',
                                       'cf-fcs_metadata = cytoflow.scripts.fcs_metadata:main'],
                  'gui_scripts' : ['cytoflow = cytoflowgui.run:run_gui']}
)
