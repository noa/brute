# -*- coding: utf-8 -*-

"""brute.status: provides entry point main()."""

import sys
import fnmatch
import os
import errno
from progress.bar import Bar
import subprocess
import argparse
import importlib
from enum import Enum
from configparser import ConfigParser
from clusterlib.scheduler import submit # for job submission
from clusterlib.scheduler import queued_or_running_jobs
from clusterlib.storage import sqlite3_loads
from util import get_conf
from .version import __version__

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('workspace')
    parser.add_argument('scraper',
                        help='scraper script which provides a [float] scrape(PATH) method')
    parser.add_argument('--brute-config')
    parser.add_argument('--max', type=int, default=15)
    parser.add_argument('-V','--version',
                        action='version',
                        version='%(prog)s (version ' + __version__ + ')')
    return parser.parse_args()

def get_param_str(path):
    lines = open(path).readlines()
    prms = lines[0].rstrip().split()[2:]
    ret = []
    i = 0
    while i < len(prms)-1:
        pname = prms[i][2:]
        ret.append(pname)
        ret.append(prms[i+1])
        i += 2
    return ' '.join(ret)

def get_job_num(s):
    head = s.rstrip('0123456789')
    tail = s[len(head):]
    return tail

def run_command(command):
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    return p.stdout.read()

def main():
    # Read arguments
    args = get_args()

    assert os.path.isdir(args.workspace), "not a directory: " + args.workspace

    # Read the configuration file
    config = get_conf(args)

    all_results = []

    # Number of iles
    nfiles = 0
    for f in os.listdir(args.workspace):
        if fnmatch.fnmatch(f, '*.params'):
            nfiles += 1

    bar = Bar('Processing', max=nfiles)

    for f in os.listdir(args.workspace):
        if fnmatch.fnmatch(f, '*.params'):
            expt_params = os.path.join(args.workspace, f)
            prm_str = get_param_str(expt_params)
            path, ext = os.path.splitext(f)
            job_num = get_job_num(path)
            expt_dir = os.path.join(args.workspace, path)
            for f2 in os.listdir(expt_dir):
                if fnmatch.fnmatch(f2, '*.txt'): # job log output
                    log = os.path.join(expt_dir, f2)
                    result = run_command([args.scraper, log])
                    if result:
                        all_results.append((result, prm_str, f))
                    else:
                        print('no result for: ' + f)
                    break
            bar.next()

    # End the progress bar
    bar.finish()

    from operator import itemgetter
    for e in sorted(all_results, key=itemgetter(0), reverse=True)[0:args.max]:
        print(' '.join([str(x) if type(x) == float else x for x in e]))
