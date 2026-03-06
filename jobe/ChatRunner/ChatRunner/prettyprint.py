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
    parser.add_argument('outfile',help="Output file")
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
        result.append( f"## Question {qno+1}" )
        result.append( "" )
        result.append( "> " + q["question"] )
        result.append( "" )
        for ano, a in enumerate( q["answers"] ):
            result.append( f"### Answer no. {qno+1}-{ano+1}" )
            result.append( "" )
            result.append( "> " + a["ans"] )
            result.append( "" )
            for fno, fb in enumerate( a["feedback"] ):
                result.append( f"#### Feedback no. {qno+1}-{ano+1}-{fno+1}" )
                result.append( "" )
                result.append( f"+ **fraction:** {fb["fraction"]:.2f}" )
                result.append( f"+ **model:** {fb["model"]}" )
                result.append( "" )
                for tno, tst in enumerate( fb["testfeedback"] ):
                    result.append( f"##### Test {tno+1}: {tst["name"]}" )
                    result.append( "" )
                    if "passed" in tst:
                        result.append( f"+ **passed:** {tst["passed"]}" )
                    if "mark" in tst:
                        result.append( f"+ **mark:** {tst["mark"]}" )
                    result.append( "" )

    with open(args.outfile, "w") as f:
        f.write("\n".join(result))

