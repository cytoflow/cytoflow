#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
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

import os
from setuptools import setup, Extension

no_logicle = os.environ.get('NO_LOGICLE', None) == 'True'

setup(
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
)
