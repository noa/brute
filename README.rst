# Brute: easy grid search ##

## Installation ##

Run:
``
python setup.py install
``
This should place the command `brute` in your path.

## Usage ##

Sample usage:

``
brute worker.py --foo 1,2,3 --bar x
``

will execute 3 tasks:

* `worker.py --foo 1 --bar x`
* `worker.py --foo 2 --bar x`
* `worker.py --foo 3 --bar x`

Each task will have a subdirectory where a run script and a log file will be created. The location where the subdirectories are created may be controlled via the `--brute-dir` flag.

Grid-specific options go in a configuration file. See
`examples/brute.conf` for an example.
