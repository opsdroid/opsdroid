#!/usr/bin/env python3
import os
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist
from setuptools.command.develop import develop
from opsdroid.const import __version__

PACKAGE_NAME = 'opsdroid'
HERE = os.path.abspath(os.path.dirname(__file__))

PACKAGES = find_packages(exclude=['tests', 'tests.*', 'modules',
                                  'modules.*', 'docs', 'docs.*'])


# For now we simply define the install_requires based on the contents
# of requirements.txt. In the future, install_requires may become much
# looser than the (automatically) resolved requirements.txt.
with open(os.path.join(HERE, 'requirements.txt'), 'r') as fh:
    REQUIRES = [line.strip() for line in fh]


class Develop(develop):
    """Custom `develop` command to always build mo files on install -e."""

    def run(self):
        self.run_command('compile_catalog')
        develop.run(self)  # old style class


class BuildPy(build_py):
    """Custom `build_py` command to always build mo files for wheels."""

    def run(self):
        self.run_command('compile_catalog')
        build_py.run(self)  # old style class


class Sdist(sdist):
    """Custom `sdist` command to ensure that mo files are always created."""

    def run(self):
        self.run_command('compile_catalog')
        sdist.run(self)   # old style class


setup(
    name=PACKAGE_NAME,
    version=__version__,
    license='Apache License 2.0',
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
    setup_requires=['Babel'],
    cmdclass={'sdist': Sdist, 'build_py': BuildPy, 'develop': Develop},
    entry_points={
        'console_scripts': [
            'opsdroid = opsdroid.__main__:main'
        ]
    },
)
