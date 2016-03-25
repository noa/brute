from configparser import ConfigParser
import sys
import os

def get_conf(args):
    config = ConfigParser()

    # Brute defaults
    config.add_section("brute")
    config.set("brute", "env", "slurm")

    # Slurm defaults
    config.add_section("slurm")
    config.set("slurm", "time", "1:00:00")
    config.set("slurm", "memory", "2000")
    config.set("slurm", "cpus-per-task", "1")
    config.set("slurm", "ntasks-per-node", "1")

    # SGE defaults
    config.add_section("sge")
    config.set("sge", "time", "1:00:00")
    config.set("sge", "memory", "1000")

    locs = None
    if args.brute_config:
        print('using configuration from: ' + args.brute_config)
        locs = [ args.brute_config ]
    else:
        locs = [ os.curdir, os.environ.get("BRUTE_CONF") ]

    for loc in locs:
        if loc is None:
            continue
        if os.path.isfile(loc):
            with open(loc) as source:
                print('reading config from: ' + loc)
                config.readfp( source )
                return config
        # otherwise its a directory
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
