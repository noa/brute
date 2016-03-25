#! /usr/bin/env python3

import argparse

def get_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('log')
    return parser

def scrape(path):
    for line in open(path):
        if line.find('result') >= 0:
            return float(line.split()[1])

if __name__ == "__main__":
    args = get_arg_parser().parse_args()
    print(scrape(args.log))

# eof
