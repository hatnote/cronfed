"""
Cronfed
=======

Cronfed is a tool for monitoring basic batch jobs, or any other
cron-based scheduled commands. For more information see the README.
"""
import os
import sys
from setuptools import setup


__author__ = 'Mahmoud Hashemi and Mark Williams'
__version__ = '0.2.1'
__contact__ = 'mahmoudrhashemi@gmail.com'
__url__ = 'https://github.com/hatnote/cronfed'
__license__ = 'BSD'


if sys.version_info >= (3,):
    raise NotImplementedError("cronfed Python 3 support still en route to your location")

CUR_PATH = os.path.dirname(os.path.abspath(__file__))

setup(name='cronfed',
      version=__version__,
      description="Bare minimum cron job monitoring for the masses.",
      long_description=open(CUR_PATH + '/README.rst').read(),
      author=__author__,
      author_email=__contact__,
      url=__url__,
      py_modules=['cronfed'],
      install_requires=['boltons==0.4.1'],
      zip_safe=True,
      license=__license__,
      platforms='any',
      classifiers=[
          'Intended Audience :: Developers',
          'Topic :: Software Development :: Libraries',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7', ]
      )
