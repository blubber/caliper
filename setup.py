
from setuptools import setup, find_packages

from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='caliper',
    version='0.0.1',

    description='Instrument your Python code',
    long_description=long_description,

    url='https://github.com/pypa/blubbr/caliper',

    author='Tiemo Kieft',
    author_email='t.kieft@isogram.nl',

    license='Apache',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    keywords='instrumentation development',
    packages=find_packages(exclude=['docs', 'tests']),
    extras_require={
        'test': ['pytest', 'coverage'],
    },)
