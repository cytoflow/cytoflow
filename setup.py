from setuptools import setup, find_packages

from __future__ import print_function
import io
import os

here = os.path.abspath(os.path.dirname(__file__))

def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read('README.md')

setup(
    name = "cytoflow",
    version = "0.1.0",
    packages = find_packages(),
    #scripts = ['say_hello.py'],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['FlowCytometryTools>=0.4',
                        'pandas>=0.15.0',
                        'numexpr>=2.1',
                        'seaborn>=0.5.0',
                        'traits>=4.0'],
      
    #include_package_data = True,
    #package_data = {
    #    '': ['*.txt', '*.rst', '*.md', '*.fcs'],
    #},

    # metadata for upload to PyPI
    author = "Brian Teague",
    author_email = "teague@mit.edu",
    description = "Python tools for quantitative, reproducible flow cytometry analysis",
    long_description = long_description,
    license = "GPLv3",
    keywords = "flow cytometry scipy",
    url = "https://github.com/bpteague/cytoflow", 
    
    # could also include long_description, download_url, classifiers, etc.
)