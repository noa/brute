# -*- coding: utf-8 -*-

"""brute.brute: provides entry point main()."""

import os
import errno
import sys
import time
import subprocess
import itertools
import glob
from configparser import ConfigParser
from blessings import Terminal # curses wrapper
import argparse                # for flexible CLI flags
import pickle

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
    
    # Any '#' characters that appear in these are replaced with
    # the task index = 1, 2, ...
    parser.add_argument('--brute-script-arg', action='append')
    
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

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}

    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def get_submission_script(cmd, name, workdir, config):
    backend=config.get("brute", "env")

    if backend == "slurm":
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

        script += " --cpus-per-task=" + str(config.getint("slurm", "cpus_per_task"))
        script += " --ntasks-per-node=" + str(config.getint("slurm", "ntasks_per_node"))

        return script

    if backend == "local":
        script = '#! /usr/bin/env sh\ncd $(dirname $0)\nCMD="%s"\n$CMD &> %s\n' % (cmd, os.path.join(workdir, "log.txt"))
        return script

    return None

def write_script_to_file(script, path):
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

            # Prepend fixed options
            if len(MyLoader.args.brute_script_arg) > 0:
                args = []
                for arg in MyLoader.args.brute_script_arg:
                    args += [ arg.replace('#',str(i)) ]
                args = ' '.join(args)
                param = args + ' ' + param

            # Write parameters to work directory
            with open( os.path.join(MyLoader.args.brute_dir, job_name+".params"), 'w' ) as f:
                f.write(param+"\n")
            
            if MyLoader.config.get("brute","env") == 'local':
                job_cmd_str = '%s %s' % (MyLoader.args.brute_script, param)
            elif MyLoader.config.get("brute","env") == 'slurm':
                job_cmd_str = 'srun %s %s' % (MyLoader.args.brute_script, param)

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

def get_conf(args):
    config = ConfigParser()

    # Brute defaults
    config.add_section("brute")
    config.set("brute", "env", "slurm")

    # Slurm defaults
    config.add_section("slurm")
    config.set("slurm", "time", "1:00:00")
    config.set("slurm", "memory", "2000")
    config.set("slurm", "cpus_per_task", "1")
    config.set("slurm", "ntasks_per_node", "1")

    locs = None
    if args.brute_config:
        print('using configuration from: ' + args.brute_config)
        locs = [ args.brute_config ]
    else:
        locs = [ os.curdir, os.environ.get("BRUTE_CONF") ]
    for loc in locs:
        if loc is None:
            continue
        try:
            with open(os.path.join(loc, "brute.conf")) as source:
                print('reading config from: ' + loc)
                config.readfp( source )
                return config
        except IOError as e:
            if args.brute_config:
                print('problem reading brute config from: ' + args.brute_config)
                print(str(e))
                sys.exit(1)
            pass
    return config

def main():
    # Get command line arguments
    args, leftovers = get_brute_args()

    if leftovers == []:
        print('no tasks to run')
        sys.exit(0)

    # Print version?
    #if args.version:
    #    print('brute version: ' + __version__)
    #    return
        
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

    #for p in params:
    #    print(p)

    print(str(len(params)) + ' tasks')
    proceed = query_yes_no("Proceed?")
    if not proceed:
        sys.exit(0)

    # Run the grid search
    loader = MyLoader()
    MyLoader.args = args
    MyLoader.params = params
    MyLoader.config = config
    sys.exit(DoitMain(loader).run(['--backend','json']))
