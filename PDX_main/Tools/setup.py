#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Project: Azimuthal integration
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import os, sys, glob
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from distutils.core import  Extension
from Cython.Distutils import build_ext

# for numpy
from numpy.distutils.misc_util import get_numpy_include_dirs

if sys.platform in ["linux2", "posix"]:
    openmp = '-fopenmp'
elif sys.platform in ["win32", "nt"]:
    openmp = '/openmp'

src = {}
cython_files = [os.path.splitext(i)[0] for i in glob.glob("*.pyx")]
if build_ext:
    for ext in cython_files:
        src[ext] = os.path.join(".", ext + ".pyx")
else:
    for ext in cython_files:
        src[ext] = os.path.join(".", ext + ".c")

marchingsquares_dict = dict(name="marchingsquares_",
                    include_dirs=get_numpy_include_dirs(),
                    sources=[src['marchingsquares_']],
                    )


setup(name='tools',
      version="0.0.0",
      author="Jerome Kieffer",
      author_email="jerome.kieffer@esrf.eu",
      description='tools for Py2Dex',
      ext_modules=[
                   Extension(**marchingsquares_dict),
                   
                   ],
      cmdclass={'build_ext': build_ext},
      )
