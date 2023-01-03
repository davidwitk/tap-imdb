from setuptools import setup

setup(
   name='tap-imdb',
   version='0.0.1',
   description='A python module to train creating packages for Singer Taps based on IMDb data',
   author='David Witkowski',
   install_requires=[
      'beautifulsoup4==4.11.1', 
      'requests==2.28.1', 
      'singer-python==5.13.0'
   ]
)
