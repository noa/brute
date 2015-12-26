# Brute: easy grid search

## Introduction

This command-line script lets you run any command with many possible
inputs in a distributed environment such as SGE, SLURM, or a local
machine with many processors. Basic checkpointing is provided via the
doit library, so that failed jobs might be re-run without re-running
all jobs.

## Installation

Run:

    python setup.py install

This should place the command `brute` in your path.

## Usage

Sample usage:

    brute worker.py --foo 1,2,3 --bar x

will execute 3 tasks:

* `worker.py --foo 1 --bar x`
* `worker.py --foo 2 --bar x`
* `worker.py --foo 3 --bar x`

Each task will have a subdirectory where a run script and a log file
will be created. The location where the subdirectories are created may
be controlled via the `--brute-dir` flag.

Grid-specific options go in a configuration file. See
`examples/brute.conf` for an example.

## Summarizing results

In addition to the `brute` command-line script, the `scrape` command
is provided to facilitate summarizing the results of large grid
jobs. This command has several uses.

1. Obtain the job return status information. Either via `--status`,
   which produces a summary of the return status, or `--status-verbose`,
   which prints the return status for all jobs.

2. For jobs which produce a single number as a result, `scrape` may be
   used to sort and summarize the jobs according to this score.  This
   is especially useful in machine learning applications. For this
   purpose, a Python script must be provided via `--scraper`. This
   script must provide the following method:

   ``
   def scrape(PATH):
      # TODO: implement code to scrape job output
      return SCORE
   ``

   The result will be the jobs and their arguments, sorted by their
   scores. The `--max` argument may be used to limit the number of
   displayed results.
