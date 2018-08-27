#!/usr/bin/env python3.4
# coding: latin-1

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

from setuptools import setup, find_packages, Extension
import io, os

import versioneer

# sphinx is only required for building packages, not for end-users
try:
    from sphinx.setup_command import BuildDoc
    has_sphinx = True
except ImportError:
    has_sphinx = False
    
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
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

# cf https://packaging.python.org/en/latest/single_source_version.html

def read_file(*names, **kwargs):
    with io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8")
    ) as fp:
        return fp.read()

long_description = read_rst('README.rst')

cmdclass = versioneer.get_cmdclass()  # @UndefinedVariable
if has_sphinx:
    cmdclass['build_sphinx'] = BuildDoc
    
setup(
    name = "cytoflow",
    version = versioneer.get_version(),  # @UndefinedVariable
    packages = find_packages(exclude = ["packaging", "packaging.qt"]),
    cmdclass = cmdclass,
    
    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['numpy==1.15.0',
                        'pandas==0.23.4',
                        'matplotlib==2.2.3',  
                        'bottleneck==1.2.1',
                        'numexpr==2.6.7',
                        'scipy==1.1.0',
                        'scikit-learn==0.19.1',
                        'seaborn==0.9.0',
                        'traits==4.6.0',
                        'pyface==6.0.0',
                        'traitsui==6.0.0',
                        'nbformat==4.4.0',
                        'python-dateutil==2.7.3',
                        'statsmodels==0.9.0',
                        'envisage==4.6.0',
                        'camel==0.1.2',
                        'yapf==0.22.0',
                        'fcsparser==0.2.0',
                        'pyopengl==3.1.1a1'] 
                if not on_rtd else ['sphinx==1.7.7'],
                        
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
                             swig_opts=['-c++'])] \
                if not (on_rtd or no_logicle) else None,
    
    package_data = { 'cytoflowgui' : ['preferences.ini',
                                      'images/*.png',
                                      'op_plugins/images/*.png',
                                      'view_plugins/images/*.png',
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
    url = "https://github.com/bpteague/cytoflow", 
    classifiers=[
                 'Development Status :: 4 - Beta',
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
                 'Programming Language :: Python :: Implementation :: CPython',
                 'Topic :: Scientific/Engineering :: Bio-Informatics',
                 'Topic :: Software Development :: Libraries :: Python Modules'],
    
    entry_points={'console_scripts' : ['cf-channel_voltages = cytoflow.scripts.channel_voltages:main',
                                       'cf-fcs_metadata = cytoflow.scripts.fcs_metadata:main'],
                  'gui_scripts' : ['cytoflow = cytoflowgui.run:run_gui']}
)
