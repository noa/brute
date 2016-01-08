# Brute: easy grid search

## Introduction

This package provides command-line scripts that make it easier to run jobs in compute grid environments such as SGE and SLURM. The package is called *brute* after "brute force" parameter searches, in which all possible parameter combinations are explored. A typical use case for this package is hyper-parameter search in machine learning applications.

## Installation

Run:

    $ python3 setup.py install --user

This will place the commands `bsubmit`, `bstatus`, and `bscrape` in your path.

## Quick Start

Under `examples/`, there are three directories for different compute environments: `local`, `sge`, and `slurm`.

Let's look at `local`. There is a script called `worker.py` which is a stand-in for what you would want to run (e.g. my_compute_job.py). It does not have to be a Python script--any command line executable works. 

The `worker.py` script will sleep for a random amount of time, then log a final number (also random) as a toy result (in practice, this might be some kind of performance metric).

The main functionality of brute is via the `bsubmit` command line script, which may be used 
as

    $ bsubmit worker.py x# y --baz yes,no --foo 10,20,30

Behind the scenes, `bsubmit` abstracts away the underlying compute environment, and submits jobs for all combinations of the arguments. The special argument `x#` tells brute to replace `#` with the job number when submitting the job to the queue, which is useful for producing output files.

While the jobs are running or after they have finished, the `bstatus` command may be used to check the logs for signs of success or failure. This command knows about queue-specific errors such as resource limits. If everything goes well:

    $ bstatus .

    JOB STATUS
    --------------------------
    STATUS:OK : 6
    --------------------------
    TOTAL: 6

Finally, `bscrape` makes it easy summarize the output of jobs run using `bsubmit`:

    $ bscrape . worker.py

    Processing |################################| 6/6
    0.9213163488004676 baz no foo 30 worker2.params
    0.920159571765027 baz yes foo 30 worker5.params
    0.8641904297067807 baz no foo 10 worker1.params
    0.5867760353344568 baz yes foo 20 worker6.params
    0.21614957715926542 baz no foo 20 worker3.params
    0.06255650484871556 baz yes foo 10 worker4.params

More details on this command are given below.

## Submitting jobs

Sample usage:

    $ bsubmit worker.py --foo 1,2,3 --bar x

will execute 3 tasks:

* `worker.py --foo 1 --bar x`
* `worker.py --foo 2 --bar x`
* `worker.py --foo 3 --bar x`

Each task will have a subdirectory where a run script and a log file
will be created. The location where the subdirectories are created may
be controlled via the `--brute-dir` flag.

Grid-specific options go in a configuration file. See
`examples/brute.conf` for an example.

## Job status

The `bstatus` command summarizes the status of jobs in the supplied path.

sample usage:

    $ bstatus .

Substitute `.` with the workspace passed to `bsubmit`, if different than the current directory.

## Summarizing results

The `bscrape` command is provided to summarize the output of jobs run via `bsubmit`
when those jobs produce a single number, such as a score or loss, as a final result.

Sample usage:

    $ bscrape . worker.py

will return the parameters and score for each job run via `bsubmit` in the current directory.
   
If `bsubmit` used another workspace, replace `.` with that workspace. The second argument
(`worker.py` above) must implement a `scrape()` method as:

    def scrape(PATH):
        # TODO: implement code to scrape job output from log to stdout/stderr
        return SCORE

The result will be the jobs and their parameters, sorted by their
scores. The `--max` argument may be used to limit the number of
displayed results.