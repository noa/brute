# Brute: easy grid search

## Introduction

This package provides command-line scripts that facilate running jobs in compute grid environments such as SGE and SLURM. The package is called *brute* after "brute force" parameter searches, in which all possible parameters are explored. A typical use case for this package is hyper-parameter search in machine learning applications.

## Installation

Run:

    python3 setup.py install --user

This will place the commands `bsubmit`, `bstatus`, and `bscrape` in your path.

## Submitting jobs

Sample usage:

    bsubmit worker.py --foo 1,2,3 --bar x

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

    bstatus .

Substitute `.` with the workspace passed to `bsubmit`, if different than the current directory.

## Summarizing results

The `bscrape` command is provided to summarize the output of jobs run via `bsubmit`
when those jobs produce a single number, such as a score or loss, as a final result.

Sample usage:

    bscrape . worker.py

will return the parameters and score for each job run via `bsubmit` in the current directory.
If `bsubmit` used another workspace, replace `.` with that workspace. The second argument
(`worker.py` above) must implement a `scrape()` method as:

    def scrape(PATH):
        # TODO: implement code to scrape job output from log to stdout/stderr
        return SCORE

The result will be the jobs and their parameters, sorted by their
scores. The `--max` argument may be used to limit the number of
displayed results.
