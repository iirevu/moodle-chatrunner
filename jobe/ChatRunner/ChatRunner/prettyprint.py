# (C) 2026: Hans Georg Schaathun <georg@schaathun.net> 

import toml
import tomllib
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
    with open( args.file, "rb" ) as f:
        feedback = tomllib.load( f )

    # feedback = toml.load( args.file )

    print( "Top level:", feedback.keys() )

    qs = feedback["questions"]
    print( "Questions", type(qs), len(qs) )
