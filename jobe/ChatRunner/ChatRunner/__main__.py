# (C) 2025: Jonas Julius Harang, Hans Georg Schaathun <hasc@ntnu.no>

"""
This is a test program to test ChatRunner without going through Moodle
and CodeRunner.

Several modes of operation.
- moodle mode runs through the sandbox (subprocess) as in CodeRunner
- debug mode (implicit in moodle mode) dumps and reparses output, as 
  required by the sandbox.
- markdown mode provides feedback in Markdown, otherwise CodeRunner format
  is used
- verbose mode adds diagnostic output
"""

from .chatrunner import *
from .sandbox import runAnswer
import json
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
    prog = 'chatrunner',
    description = 'Get AI feedback on a student answer',
             epilog = '')
    parser.add_argument('problem',help="Problem file")
    parser.add_argument('answer',help="Answer file")
    parser.add_argument('-m','--model',help="Model")
    parser.add_argument('-l','--literature',help="Literature file (json)")
    parser.add_argument('-u','--url',help="URL for the LLM OpenAPI.")
    parser.add_argument('-k','--api-key',dest="key",help="Key for API access.")
    parser.add_argument('-A','--api',help="The API to use for AI connection.")
    parser.add_argument('-C','--config',help="Config file (json).")
    parser.add_argument('-M','--moodle',action="store_true",
                        help="Moodle mode, running in the sandbox.")
    parser.add_argument('-v','--verbose',action="store_true",
                        help="Verbose/debug mode.")
    parser.add_argument('-p','--markdown',action="store_true",
                        help="Markdown output.")
    parser.add_argument('-D','--debug',action="store_true",
                        help="Debug mode.")
    args = parser.parse_args()

    # Read support files
    with open(args.problem, 'r') as file:
        prob = file.read()
    with open(args.answer, 'r') as file:
        ans = file.read()
    if args.literature:
        with open(args.literature, 'r') as file:
            lit = file.read()
    else: lit = {}
    
    # Read AI configuration from JSON or from arguments 
    if args.config:
        with open( args.config, "r" ) as file:
            cfg = json.load(file)
    else:
        cfg = {}

    # Arguments override file.
    if args.api:
        cfg["API"] = args.api
    if args.key:
        cfg["OPENAI_API_KEY"] = args.key
    if args.url:
        cfg["url"] = args.url
    if args.model:
        cfg["model"] = args.model

    # Set default URLs
    if cfg.get( "url" ) is None: 
        api = cfg["api"]
        if api == "ollama":
           cfg["url"] = "http://localhost:11434/api/chat"
        elif api == "openai":
           cfg["url"] = "https://api.openai.com/v1/chat/completions"
        else:
            raise Exception( "No URL provided." )

    print( cfg )

    # Support for graderstate is currently not implemented; use a blank.
    graderstate_string = ""

    # Run the test
    if args.moodle:
        r = runAnswer( prob, ans, lit, graderstate_string, cfg, debug=args.verbose, markdown=args.markdown ) 
        print( "== Output of runAnswer ==" )
        print( r )
    else:
        r = testProgram( prob, ans, lit, graderstate_string, cfg, debug=args.verbose, dumpmode=args.debug, markdown=args.markdown )
        print( r )
