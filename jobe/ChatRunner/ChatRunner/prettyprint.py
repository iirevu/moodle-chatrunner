# (C) 2026: Hans Georg Schaathun <georg@schaathun.net> 

import toml
import tomllib
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog = 'ChatRunner.prettyprint',
        description = 'Pretty print AI feedback from TOML output',
        epilog = '')
    parser.add_argument('outfile',help="Output file")
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
    result = [ "# ChatRunner test", "" ]
    for qno, q in enumerate(qs):
        result.append( f"## Question {qno}" )
        result.append( "" )
        result.append( "> " + q["question]" )
        result.append( "" )
        for ano, a in enumerate( q["answers"] ):
            result.append( f"### Answer no. {qno}-{rno}" )
            result.append( "" )
            result.append( "> " + a["ans]" )
            result.append( "" )
    with open(args.outfile, "w") as f:
        f.write("\n".join(result))

