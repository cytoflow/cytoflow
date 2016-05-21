#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
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

from __future__ import print_function
from setuptools import setup, find_packages, Extension
import io, os, re

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
no_logicle = os.environ.get('NO_LOGICLE', None) == 'True'

print(os.environ)

here = os.path.abspath(os.path.dirname(__file__))

def read_rst(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

# cf https://packaging.python.org/en/latest/single_source_version.html

def read_file(*names, **kwargs):
    with io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8")
    ) as fp:
        return fp.read()
    
def find_version(*file_paths):
    version_file = read_file(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

long_description = read_rst('README.rst')

setup(
    name = "cytoflow",
    version = find_version("cytoflow", "__init__.py"),
    packages = find_packages(),
    
    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['pandas>=0.18.0',
                        'bottleneck>=1.0',
                        'fcsparser>=0.1.1',
                        'numpy>=1.9.0',
                        'numexpr>=2.4.6',
                        'matplotlib>=1.4.3',
                        'scipy>=0.14',
                        'scikit-learn>=0.16',
                        'seaborn>=0.7.0',
                        'pyface==4.4.0',
                        'envisage>=4.0',
                        'nbformat>=4.0',
                        'python-dateutil>=2.5.2',
                        'statsmodels>=0.6.1'] \
                if not on_rtd else None,
                        
                        # ALSO requires PyQt4 >= 4.10, but it's not available
                        # via pypi and distutils.  Install it locally!
                        
    # try to build the Logicle extension
    ext_modules = [Extension("cytoflow.utility.logicle_ext._Logicle",
                             sources = ["cytoflow/utility/logicle_ext/FastLogicle.cpp",
                                        "cytoflow/utility/logicle_ext/Logicle.cpp",
                                        "cytoflow/utility/logicle_ext/Logicle.i"],
                             depends = ["cytoflow/utility/logicle_ext/FastLogicle.cpp",
                                        "cytoflow/utility/logicle_ext/Logicle.cpp",
                                        "cytoflow/utility/logicle_ext/Logicle.i",
                                        "cytoflow/utility/logicle_ext/logicle.h"],
                             swig_opts=['-c++'])] \
                if not (on_rtd or no_logicle) else None,
    
    package_data = { 'cytoflowgui' : ['preferences.ini',
                                      'images/*.png',
                                      'op_plugins/images/*.png',
                                      'view_plugins/images/*.png']},

    # metadata for upload to PyPI
    author = "Brian Teague",
    author_email = "bpteague@gmail.edu",
    description = "Python tools for quantitative, reproducible flow cytometry analysis",
    long_description = long_description,
    license = "GPLv2",
    keywords = "flow cytometry scipy",
    url = "https://github.com/bpteague/cytoflow", 
    classifiers=[
                 'Development Status :: 3 - Alpha',
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
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: Implementation :: CPython',
                 'Topic :: Scientific/Engineering :: Bio-Informatics',
                 'Topic :: Software Development :: Libraries :: Python Modules'],
    
    entry_points={'gui_scripts' : ['cytoflow = cytoflowgui:run_gui'],
                  'nose.plugins.0.10' : ['mplplugin = nose_plugins:MplPlugin']}
)
