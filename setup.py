#!/usr/bin/env python3
from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist
from setuptools.command.develop import develop
from setuptools.config import read_configuration
from itertools import chain
import versioneer


class Develop(develop):
    """Custom `develop` command to always build mo files on install -e."""

    def run(self):
        self.run_command("compile_catalog")
        develop.run(self)  # old style class


class BuildPy(build_py):
    """Custom `build_py` command to always build mo files for wheels."""

    def run(self):
        self.run_command("compile_catalog")
        build_py.run(self)  # old style class


class Sdist(sdist):
    """Custom `sdist` command to ensure that mo files are always created."""

    def run(self):
        self.run_command("compile_catalog")
        sdist.run(self)  # old style class


extras = read_configuration("setup.cfg")["options"]["extras_require"]
extras["all"] = list(chain(*extras.values()))

setup(
    extras_require=extras,
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(
        {"sdist": Sdist, "build_py": BuildPy, "develop": Develop}
    ),
)
