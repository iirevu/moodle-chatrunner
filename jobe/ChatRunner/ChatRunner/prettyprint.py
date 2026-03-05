# (C) 2026: Hans Georg Schaathun <georg@schaathun.net> 

import toml
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog = 'ChatRunner.prettyprint',
        description = 'Pretty print AI feedback from TOML output',
        epilog = '')
    parser.add_argument('file',help="Feedback file")
    args = parser.parse_args()

    if args.file is None:
        raise Exception( "No file given" )
    feedback = toml.load( args.file )

    print( "Top level:", feedback.keys )

    qs = toml["questions"]
    print( "Questions", type(qs), len(qs) )
