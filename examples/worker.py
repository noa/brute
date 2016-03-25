#! /usr/bin/env python3

import os
import argparse
import random
import time

def get_arg_parser():
    parser = argparse.ArgumentParser()

    # Grid search is over int, float, or choice arguments
    parser.add_argument('x')
    parser.add_argument('y')
    parser.add_argument('--foo', default=10, type=int)
    parser.add_argument('--bar', default=3.14, type=float)
    parser.add_argument('--baz', choices=['yes','no'], required=True)

    # String arguments are forwarded
    parser.add_argument('--boo', type=str)

    return parser

if __name__ == "__main__":
    args = get_arg_parser().parse_args()
    print(os.path.basename(__file__) + ' called with: ')
    print(args.x)
    print(args.y)
    for k, v in vars(args).items():
        print('\t' + k + ' = ' + str(v))
    print('running...')
    time.sleep(random.randint(0,10))
    print('DONE!')
    result = random.random()
    print('result ' + str(result) )

# eof
