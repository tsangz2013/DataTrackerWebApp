#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='proj',
      packages=find_packages(),
      package_data={'proj': ['*.json', "*.txt"]})