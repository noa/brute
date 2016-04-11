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
from tabulate import tabulate
from enum import Enum
from configparser import ConfigParser
from clusterlib.scheduler import submit # for job submission
from clusterlib.scheduler import queued_or_running_jobs
from clusterlib.storage import sqlite3_loads
from .version import __version__

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('workspace')
    parser.add_argument('scraper',
                        help='scraper script which provides a [float] scrape(PATH) method')
    parser.add_argument('--max', type=int, default=100)
    parser.add_argument('-V','--version',
                        action='version',
                        version='%(prog)s (version ' + __version__ + ')')
    return parser.parse_args()

def get_param_str(path):
    lines = open(path).readlines()
    return lines[0].rstrip()

def get_job_num(s):
    head = s.rstrip('0123456789')
    tail = s[len(head):]
    return tail

def run_command(command):
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    return float(p.stdout.read())

def main():
    # Read arguments
    args = get_args()

    assert os.path.isdir(args.workspace), "not a directory: " + args.workspace

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
            foundLog = False
            for f2 in os.listdir(expt_dir):
                if fnmatch.fnmatch(f2, '*.txt'): # job log output
                    log = os.path.join(expt_dir, f2)
                    result = run_command([args.scraper, log])
                    foundLog = True
                    if result:
                        all_results.append((result, prm_str, f, 'OK'))
                    else:
                        all_results.append((-float("inf"), prm_str, f, 'NORESULT'))
                    break
            # Job not run yet
            if not foundLog:
                all_results.append((-float("inf"), prm_str, f, 'NOLOG'))
            bar.next()

    # End the progress bar
    bar.finish()

    if len(all_results) < 1:
        print('No results!')

    #print(all_results)
    
    from operator import itemgetter
    sorted_results = sorted(all_results, key=itemgetter(0), reverse=True)[0:args.max]

    # Format the results into a table
    table = []
    for e in sorted_results:
        entry = [ e[0] ]
        tokens = e[1].split()
        for i in range(len(tokens)):
            if i % 2 == 1:
                entry += [ tokens[i] ]
        table += [ entry ]

    # Get the headers
    headers = [ 'score' ]
    for e in sorted_results:
        tokens = e[1].split()
        assert(len(tokens) % 2 == 0)
        for i in range(len(tokens)):
            if i % 2 == 0:
                headers += [ tokens[i] ]
        break

    #print(headers)
    #print(table)
    
    # Prune the table
    toDelete = set()
    for col in range(len(headers)):
        firstVal = table[0][col]
        allSame = True
        for row in range(1, len(table)):
            if not table[row][col] == firstVal:
                allSame = False
                break
        if allSame and col > 0:
            toDelete.add(col)

    # Make the pruned headers and table
    pruned_table = []
    for row in table:
        pruned_table.append([])
    pruned_headers = []
    for col in range(len(headers)):
        if not col in toDelete:
            pruned_headers.append(headers[col])
        for row in range(len(table)):
            if not col in toDelete:
                pruned_table[row].append(table[row][col])

    headers = pruned_headers
    table = pruned_table

    # Add status information
    headers.append('status')
    for i in range(len(table)):
        table[i].append( sorted_results[i][-1] )

    # Clean up header
    for i in range(len(headers)):
        if headers[i].startswith('--'):
            headers[i] = headers[i][2:]
        
    #print(headers)
    #print(table[0])
    assert(len(headers) == len(table[0]))
    print(tabulate(table, headers, tablefmt="simple"))
