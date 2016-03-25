# -*- coding: utf-8 -*-

"""brute.brute: provides entry point main()."""

import os
import errno
import sys
import time
import subprocess
import itertools
import glob
from prompter import prompt, yesno
from configparser import ConfigParser
import argparse                # for flexible CLI flags
import pickle

from util import get_conf

from .version import __version__

from clusterlib.scheduler import submit # for job submission
from clusterlib.scheduler import queued_or_running_jobs
from clusterlib.storage import sqlite3_loads

from doit.cmd_base import ModuleTaskLoader
from doit.cmd_base import TaskLoader
from doit.doit_cmd import DoitMain
from doit.action import CmdAction
from doit.task import dict_to_task
from doit.task import Task

def get_brute_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('brute_script')

    parser.add_argument('-V', '--version',
                        action='version',
                        version='%(prog)s (version ' + __version__ + ')')
    parser.add_argument('--brute-no-prompt', action='store_true')

    # Any '#' characters that appear in these are replaced with
    # the task index = 1, 2, ...
    # parser.add_argument('--brute-script-arg', action='append', default=[])

    parser.add_argument('--brute-dir', default=".")
    parser.add_argument('--brute-config')
    return parser.parse_known_args() # returns a tuple

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def get_submission_script(cmd, name, workdir, config):
    backend=config.get("brute", "env")
    assert cmd
    assert name
    script = None
    if backend == "sge":
        script = submit(cmd,
                        job_name=name,
                        time=config.get("sge","time"),
                        memory=config.getint("sge","memory"),
                        backend=backend,
                        log_directory=workdir)
    elif backend == "slurm":
        script = submit(cmd,
                        job_name=name,
                        time=config.get("slurm","time"),
                        memory=config.getint("slurm","memory"),
                        backend=backend,
                        log_directory=workdir)

        if config.has_option("slurm","gres"):
            script += " --gres=" + config.get("slurm", "gres")

        if config.has_option("slurm","partition"):
            script += " --partition=" + config.get("slurm", "partition")

        script += " --cpus-per-task=" + str(config.getint("slurm", "cpus-per-task"))
        script += " --ntasks-per-node=" + str(config.getint("slurm", "ntasks-per-node"))

    elif backend == "local":
        script = '#! /usr/bin/env sh\ncd $(dirname $0)\nCMD="%s"\n$CMD &> %s\n' % (cmd, os.path.join(workdir, "log.txt"))
    else:
        print("[fatal] unknown backend: " + str(backend))
        sys.exit(1)

    return script

def write_script_to_file(script, path):
    #print(type(script))
    #print(script)
    f = open(path, 'w')
    f.write(script)
    f.close()

class MyLoader(TaskLoader):
    @staticmethod
    def load_tasks(cmd, opt_values, pos_args):
        task_list = []
        i = 0

        # Make workspace
        mkdir_p(MyLoader.args.brute_dir)

        # Job task names
        job_names = []

        # Basename
        base_name = os.path.splitext(os.path.basename(MyLoader.args.brute_script))[0]

        # Run jobs
        for param in MyLoader.params:
            i+=1
            job_name = base_name + str(i)
            job_names += [job_name]
            job_cmd_str = None

            # Prepend fixed options:
            if len(MyLoader.args.brute_script_arg) > 0:
                args = []
                for arg in MyLoader.args.brute_script_arg:
                    args += [ arg.replace('#',str(i)) ]
                args = ' '.join(args)
                param = args + ' ' + param

            # Replace any # symbols in param with job index:
            param = param.replace('#',str(i))

            # Write parameters to work directory:
            with open( os.path.join(MyLoader.args.brute_dir, job_name+".params"), 'w' ) as f:
                f.write(param+"\n")

            e = MyLoader.config.get("brute","env")
            if e == 'local':
                job_cmd_str = '%s %s' % (MyLoader.args.brute_script, param)
            elif e == 'slurm':
                job_cmd_str = 'srun %s %s' % (MyLoader.args.brute_script, param)
            elif e == 'sge':
                job_cmd_str = '%s %s' % (MyLoader.args.brute_script, param)
            else:
                print("[FATAL] unknown env: " + str(e))
                sys.exit(1)

            # Job work directory
            job_work_dir = os.path.join(MyLoader.args.brute_dir, job_name)

            # Make job work dir
            mkdir_task = {
                'name': 'mkdir' + str(i),
                'actions':  [ (mkdir_p, [job_work_dir]) ],
            }
            task_list.append(dict_to_task(mkdir_task))

            # Write the job script
            script = get_submission_script(job_cmd_str,
                                           job_name,
                                           job_work_dir,
                                           MyLoader.config)

            # Write script task
            script_path = os.path.join(job_work_dir, "run.sh")

            write_script_task = {
                'name': 'script' + str(i),
                'actions': [ (write_script_to_file, [script, script_path]) ],
            }
            task_list.append(dict_to_task(write_script_task))

            # Run script job
            run_script = {
                'name': 'run' + str(i),
                'actions': [ "sh %s" % (script_path) ],
                'targets': []
            }
            task_list.append(dict_to_task(run_script))

        #print(task_list)
        config = {'verbosity': 2}
        return task_list, config

def get_job_params(leftovers):
    assert len(leftovers) % 2 == 0, 'uneven number of left-over arguments'

    params = []
    leftovers_dict = dict()
    i = 0
    while i < len(leftovers):
        key = leftovers[i]
        val = leftovers[i+1]
        vals = None

        if val.find(",") >= 0:
            vals = val.split(",")
        else:
            vals = [val]

        if key in leftovers_dict:
            for val in vals:
                leftovers_dict[key] += [val]
        else:
            leftovers_dict[key] = vals

        i += 2

    list_of_lists = []
    for key, vals in leftovers_dict.items():
        lst = []
        for val in set(vals):
            lst.append((key,val))
        list_of_lists.append(lst)

    combs = list(itertools.product(*list_of_lists))
    params = []
    for c in combs:
        tokens = []
        for x in c:
            tokens.append(x[0])
            tokens.append(x[1])
        pstr = " ".join(tokens)
        params.append(pstr)

    return params

def is_script_arg(t):
    if t.startswith('-') or t.startswith('--'):
        return False
    return True

def main():
    # Get command line arguments
    args, leftovers = get_brute_args()

    # Pop the script arguments from leftovers
    args.brute_script_arg = []
    while len(leftovers) > 0 and is_script_arg(leftovers[0]):
        args.brute_script_arg += [ leftovers.pop(0) ]

    # Read the configuration file, if any
    config = get_conf(args)

    # Get absolute workspace path
    args.brute_dir = os.path.abspath(args.brute_dir)
    print('workspace = ' + args.brute_dir)

    # Get absolute script path
    args.brute_script = os.path.abspath(args.brute_script)
    print('script = ' + args.brute_script)

    # Get the product of parameters
    params = get_job_params(leftovers)

    print(str(len(params)) + ' tasks')
    #print('tasks:')
    #print(params)

    if not args.brute_no_prompt:
        proceed = yesno('Submit?')
        if not proceed:
            sys.exit(0)

    # Run the grid search
    loader = MyLoader()
    MyLoader.args = args
    MyLoader.params = params
    MyLoader.config = config
    sys.exit(DoitMain(loader).run(['--backend','json']))
