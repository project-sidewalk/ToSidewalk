from setuptools import setup
import codecs
import os
import re

import ToSidewalk

# Code and directory structure from:
# http://www.jeffknupp.com/blog/2013/08/16/open-sourcing-a-python-project-the-right-way/
# https://github.com/jeffknupp/sandman/blob/develop/setup.py

here = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
    # intentionally *not* adding an encoding option to open
    return codecs.open(os.path.join(here, *parts), 'r').read()

def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

setup(
    name='ToSidewalk',
    version=find_version('ToSidewalk', '__init__.py'),
    url='',
    license='Apache Software License',
    author='Zachary Lawrence and Kotaro Hara',
    tests_require=['pytest'],
    install_requires=['basemap>=1.0.7',
                      'GeoAlchemy2>=0.2.5',
                      'numpy>=1.9.2',
                      'rtree>=0.8.2',
                      'shapely>=1.5.8'
                      ],
    cmdclass={},
    author_email='koe.bluebear@gmail.com',
    description='The program generates potential sidewalk network from OpenStreetMap street data',
    long_description='',
    packages=['ToSidewalk'],
    include_package_data=True,
    platforms='any',
    test_suite='',
    classifiers=[],
    extra_require={}
)
