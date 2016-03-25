#! /usr/bin/env sh

bsubmit --brute-config slurm.conf --brute-dir slurm worker.py x# y --baz yes,no --foo 10,20,30

# eof
