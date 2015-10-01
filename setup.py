# -*- coding: utf-8 -*-

"""setup.py: brute control."""

import re
from setuptools import setup

exec(open('brute/version.py').read())
with open("README.rst", "rb") as f:
    long_descr = f.read().decode("utf-8")

    setup(
        name = "cmdline-brute",
        license = "MIT",
        packages = ["brute"],
        install_requires = ["clusterlib", "doit", "blessings"],
        entry_points = {
            "console_scripts": ['brute = brute.brute:main']
        },
        version = __version__,
        description = "Brute force grid search",
        long_description = long_descr,
        author = "Nicholas Andrews",
        author_email = "noandrews@gmail.com",
        url = "https://bitbucket.org/noandrews/brute",
    )
