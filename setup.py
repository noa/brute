# -*- coding: utf-8 -*-

"""setup.py: brute control."""

import re
from setuptools import setup

version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('brute/brute.py').read(),
    re.M
    ).group(1)

with open("README.rst", "rb") as f:
    long_descr = f.read().decode("utf-8")

    setup(
        name = "cmdline-brute",
        packages = ["brute"],
        install_requires = ["clusterlib", "doit", "blessings"],
        entry_points = {
            "console_scripts": ['brute = brute.brute:main']
        },
        version = version,
        description = "Brute force grid search",
        long_description = long_descr,
        author = "Nicholas Andrews",
        author_email = "noandrews@gmail.com",
        url = "https://bitbucket.org/noandrews/brute",
    )
