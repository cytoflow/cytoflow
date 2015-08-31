from __future__ import print_function
from setuptools import setup, find_packages, Extension
import io, os, re

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
    include_package_data=True,
    
    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['pandas>=0.15.0',
                        'FlowCytometryTools>=0.4',
                        'numexpr>=2.1',
                        'matplotlib>=1.4.3',
                        'seaborn>=0.6.0',
                        'pyface>=4.0',
                        'envisage>=4.0'],
                        
                        # ALSO requires PyQt4 >= 4.10, but it's not available
                        # via pypi and distutils.  Install it locally!
                        
    # try to build the Logicle extension
    ext_modules = [Extension("cytoflow.operations.logicle_ext._Logicle",
                             sources = ["cytoflow/operations/logicle_ext/FastLogicle.cpp",
                                        "cytoflow/operations/logicle_ext/Logicle.cpp",
                                        "cytoflow/operations/logicle_ext/Logicle.i"],
                             depends = ["cytoflow/operations/logicle_ext/FastLogicle.cpp",
                                        "cytoflow/operations/logicle_ext/Logicle.cpp",
                                        "cytoflow/operations/logicle_ext/Logicle.i"],
                             swig_opts=['-c++'])],

    # metadata for upload to PyPI
    author = "Brian Teague",
    author_email = "teague@mit.edu",
    description = "Python tools for quantitative, reproducible flow cytometry analysis",
    long_description = long_description,
    license = "GPLv3",
    keywords = "flow cytometry scipy",
    url = "https://github.com/bpteague/cytoflow", 
    classifiers=[
                 'Development Status :: 2 - Pre-Alpha',
                 'Environment :: Console',
                 'Environment :: MacOS X',
                 'Environment :: Win32 (MS Windows)',
                 'Environment :: X11 Applications :: Qt',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
                 'Natural Language :: English',
                 'Operating System :: MacOS',
                 'Operating System :: Microsoft :: Windows',
                 'Operating System :: POSIX :: Linux',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: Implementation :: CPython',
                 'Topic :: Scientific/Engineering :: Bio-Informatics'],
    
    entry_points={'gui_scripts' : ['cytoflow = cytoflowgui:run_gui']}
)
