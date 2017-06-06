#!/usr/bin/env python3
import os
from setuptools import setup, find_packages
from opsdroid.const import __version__

PACKAGE_NAME = 'opsdroid'
HERE = os.path.abspath(os.path.dirname(__file__))

PACKAGES = find_packages(exclude=['tests', 'tests.*', 'modules',
                                  'modules.*', 'docs', 'docs.*'])

REQUIRES = [
    'arrow==0.10.0',
    'aiohttp==2.1.0',
    'pycron==0.40',
    'pyyaml==3.12'
]

setup(
    name=PACKAGE_NAME,
    version=__version__,
    license='GNU GENERAL PUBLIC LICENSE V3',
    url='',
    download_url='',
    author='Jacob Tomlinson',
    author_email='jacob@tom.linson.uk',
    description='An open source chat-ops bot.',
    packages=PACKAGES,
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=REQUIRES,
    test_suite='tests',
    keywords=['bot', 'chatops'],
    entry_points={
        'console_scripts': [
            'opsdroid = opsdroid.__main__:main'
        ]
    },
)
