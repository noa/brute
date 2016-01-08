# -*- coding: utf-8 -*-

"""brute.status: provides entry point main()."""

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

class Status(Enum):
    ok = 1,
    memory = 2,
    nonzero = 3

    def __str__(self):
        if self.name == 'ok':
            return 'STATUS:OK'
        if self.name == 'memory':
            return 'STATUS:ERROR:MEMORY'
        if self.name == 'nonzero':
            return 'STATUS:ERROR:NONZERO'

def get_job_status(path, config):
    for line in open(path):
        if line.find('Exceeded job memory limit') >= 0:
            return Status.memory
        if line.find('Exited with exit code') >= 0:
            return Status.nonzero
    return Status.ok
        
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('workspace')
    parser.add_argument('--brute-config')
    parser.add_argument('--verbose',
                        action='store_true',
                        help='show the return status of all jobs')
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

def main():
    # Read arguments
    args = get_args()

    assert os.path.isdir(args.workspace), "not a directory: " + args.workspace
    
    # Read the configuration file
    config = get_conf(args)

    # Dictionary to store job results
    job_status = dict()

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
                    status = get_job_status(log, config)
                    job_status[job_num] = status
                    break
            bar.next()

    # End the progress bar
    bar.finish()

    if args.verbose:
        for n in job_status:
            print('n='+n+' status='+str(job_status[n]))

    if True:
        print('JOB STATUS')
        print('--------------------------')
        import collections
        stats = collections.defaultdict(int)
        for n in job_status:
            stats[job_status[n]] += 1
        total = 0
        for k in stats:
            total += stats[k]
            print(str(k) + ' : ' + str(stats[k]))
        print('--------------------------')
        print('TOTAL: ' + str(total))    
