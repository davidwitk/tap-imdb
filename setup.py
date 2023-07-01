#!/usr/bin/env python
from setuptools import setup

setup(
   name='tap-imdb',
   version='0.1.0',
   description='A python module to train creating packages for Singer Taps based on IMDb data',
   author='David Witkowski',
	classifiers=["Programming Language :: Python :: 3 :: Only"],
   install_requires=[
      'beautifulsoup4==4.11.1', 
      'singer-python==5.13.0',
      'selenium==4.10.0'
   ],
   packages=["tap_imdb"],
   package_dir={"tap_imdb": "tap_imdb"},
   entry_points={
      'console_scripts': ['tap-imdb=tap_imdb:main']
   }
)
