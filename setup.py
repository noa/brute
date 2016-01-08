# -*- coding: utf-8 -*-

"""setup.py: brute control."""

import re
from setuptools import setup

exec(open('brute/version.py').read())

try:
    import pypandoc
    description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
    print('error converting README')
    description = ''

setup(
    name = "cmdline-brute",
    license = "MIT",
    packages = ["brute"],
    py_modules = ["util"],
    install_requires = ["clusterlib", "doit", "progress"],
    entry_points = {
        "console_scripts": ['bsubmit = brute.submit:main',
                            'bstatus = brute.status:main',
                            'bscrape = brute.scrape:main']
    },
    version = __version__,
    description = "BRUTE FORCE grid search",
    long_description = description,
    author = "Nicholas Andrews",
    author_email = "noandrews@gmail.com",
    url = "https://bitbucket.org/noandrews/brute",
)


