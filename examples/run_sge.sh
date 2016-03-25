#! /usr/bin/env sh

bsubmit --brute-config sge.conf --brute-dir sge worker.py x# y --baz yes,no --foo 10,20,30

# eof
