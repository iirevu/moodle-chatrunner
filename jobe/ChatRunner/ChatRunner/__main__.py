# (C) 2025: Jonas Julius Harang, Hans Georg Schaathun <hasc@ntnu.no>

"""
This is a test program to test ChatRunner without going through Moodle
and CodeRunner.
"""

from .chatrunner import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
    prog = 'chatrunner',
    description = 'Get AI feedback on a student answer',
             epilog = '')
    parser.add_argument('problem',help="Problem file")
    parser.add_argument('answer',help="Answer file")
    parser.add_argument('-m','--model',default="gpt-oss:20b",help="Model")
    parser.add_argument('-l','--literature',help="Literature file (json)")
    parser.add_argument('-u','--url',help="URL for the LLM OpenAPI.")
    parser.add_argument('-k','--api-key',dest="key",help="Key for API access.")
    parser.add_argument('-A','--api',help="The API to use for AI connection.")
    parser.add_argument('-T','--test',action="store_true",
                        help="Debug mode, running without the sandbox.")
    args = parser.parse_args()
    with open(args.problem, 'r') as file:
        prob = file.read()
    with open(args.answer, 'r') as file:
        ans = file.read()
    
    if args.literature:
        with open(args.literature, 'r') as file:
            lit = file.read()
    else: lit = {}
    graderstate_string = ""
    sandboxparams = {}
    if args.api:
        sandboxparams["API"] = args.api
        if args.api == "ollama":
           sandboxparams["url"] = "http://localhost:11434/api/chat"
        elif args.api == "openai":
           sandboxparams["url"] = "https://api.openai.com/v1/chat/completions"
    print( args.api )
    print( sandboxparams )
    if args.key:
        sandboxparams["OPENAI_API_KEY"] = args.key
    if args.url:
        sandboxparams["url"] = args.url
    if args.model:
        sandboxparams["model"] = args.model

    if args.test:
        r = testProgram( prob, ans, lit, graderstate_string, sandboxparams )
        print( "== Output of testProgram ==" )
        print( "Fraction:", r.get( "fraction" ) )
        print( r.get( "prologuehtml" ) )
        print( "== Test Results ==" )
        # Table coded as list of lists
        print( r.get( "testresults" ) )
        print( "== Graderstate ==" )
        print( r.get( "graderstate" ) )
        print( r.get( "epiloguehtml" ) )
    else:
        r = runAnswer( prob, ans, lit, graderstate_string, sandboxparams, debug=True ) 
        print( "== Output of runAnswer ==" )
        print( r )
