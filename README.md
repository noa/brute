# Brute: easy grid search

## Introduction

This package provides command-line scripts that make it easier to run
jobs in compute grid environments such as SGE and SLURM. The package
is called *brute* after "brute force" parameter searches, in which all
possible parameter combinations are explored. A typical use case for
this package is hyper-parameter search in machine learning
applications.

## Installation

Run:

    $ python setup.py install --user

This will place the commands `bsubmit`, `bstatus`, and `bscrape` in your path.

## Example Usage

### bsubmit

The main functionality is provided by `bsubmit` command line script,
with the following example usage:

    $ bsubmit worker.py x# y --baz yes,no --foo 10,20,30

The `bsubmit` submits jobs for all combinations of the arguments. The
special argument `x#` tells brute to replace `#` with the job number
when submitting the job to the queue, which is useful for producing
output files. This produces:

    worker1/
    worker1.params
    worker2/
    worker2.params
    [...]

Under `examples/`, there are three scripts to run examples under
different compute environments: `run_local.sh`, `run_sge.sh`, and
`run_slurm.sh`. The only difference between these scripts are the
configuration files (the corresponding `*.conf` files)

The `worker.py` script will sleep for a random amount of time, then
log a final number (also random) as a toy result (in practice, this
might be some kind of performance metric).

### bstatus

While the jobs are running or after they have finished, the `bstatus`
command may be used to check the logs for signs of success or
failure. This command knows about queue-specific errors such as
resource limits. If everything goes well:

    $ bstatus .

    JOB STATUS
    --------------------------
    STATUS:OK : 6
    --------------------------
    TOTAL: 6

The `bstatus` command summarizes the status of jobs in the supplied
path.  Substitute the first argument (`.` above) with the
`--brute-dir` passed to `bsubmit` if not the current directory.

### bscrape

Finally, `bscrape` makes it easy summarize the output of jobs run
using `bsubmit`:

    $ bscrape local scraper.py

    Processing |################################| 6/6
    0.9213163488004676 baz no foo 30 worker2.params
    0.920159571765027 baz yes foo 30 worker5.params
    0.8641904297067807 baz no foo 10 worker1.params
    0.5867760353344568 baz yes foo 20 worker6.params
    0.21614957715926542 baz no foo 20 worker3.params
    0.06255650484871556 baz yes foo 10 worker4.params

The arguments are:

    $ bscrape RESULT_DIRECTORY SCRAPE_COMMAND

where `RESULT_DIRECTORY` is usually the value passed to the
`--brute-dir` argument of `bsubmit`.

The displayed output is a list of jobs and their parameters, sorted by
the scores which are extracted via `scraper.py` (which is job specific
and may be any command line argument).
