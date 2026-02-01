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

import toml
from . import helper

def batchfeedback( *a, config={}, **kw ):
    r = testProgram( *a, config=config, **kw )
    r["model"] = config["model"]
    return r

def batchprocess( qalist, lit, cfg, count, **kw ):
    modellist = cfg["model"]
    try:
        _ = iter(modellist)
    except:
        modellist = [ modellist ]
    config = []
    for m in modellist:
        c = cfg.copy()
        c["model"] = m
        config.append( c )
    for q in qalist["questions"]:
        prob = q["question"]
        for a in q["answers"]:
            ans = a["ans"]
            criteria = a.get( "criteria", "" )
            a["feedback"] = [ batchfeedback( prob, ans, lit
                            , config=config, criteria=criteria, **kw ) 
                            for _ in range(count) ]
    return qalist

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
    prog = 'chatrunner',
    description = 'Get AI feedback on a student answer',
             epilog = '')
    parser.add_argument('problem',help="Problem file",nargs="?")
    parser.add_argument('answer',help="Answer file",nargs="?")
    parser.add_argument('criteria',help="Answer file",nargs="?")
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
    parser.add_argument('-o','--outfile',
                        help="Filename for JSON output.")
    parser.add_argument('-E','--mode',default="baseline",
                        help="Engine mode (baseline/dump/new).")
    parser.add_argument('-b','--batch',
                        help="Question/answer set for batch ruin (toml file).")
    parser.add_argument('-n','--count',default=1,
                        help="Numer of repetition of the batch test.")
    args = parser.parse_args()

    if args.batch:
        with open(args.batch, "rb") as f:
            print( "Opened file", args.batch )
            qalist = toml.load(f)
    else:
        # Read support files
        if args.problem is None:
            raise Exception("Needs problem and answer arguments.")
        if args.answer is None:
            raise Exception("Needs answer argument.")
        with open(args.problem, 'r') as file:
            prob = file.read()
        with open(args.answer, 'r') as file:
            ans = file.read()
        if args.criteria:
            with open(args.criteria, 'r') as file:
                criteria = file.read()
        else:
            criteria = ""
    if args.literature:
        with open(args.literature, 'r') as file:
            lit = file.read()
    else: lit = {}
    
    # Read AI configuration from JSON or from arguments 
    if args.config:
        cfg = helper.readobject( args.config )
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

    if args.debug:
        mode = "dump"
    if args.moodle:
        mode = "moodle"
    else:
        mode = args.mode

    # Run the test
    if args.batch:
        r = batchprocess( qalist, lit, cfg=cfg, count=int(args.count)
                        , gs=graderstate_string, mode=mode )
        with open(args.outfile, "wb") as f:
             toml.dump(qalist,f)
    elif mode == "moodle":
        r = runAnswer( prob, ans, lit, criteria, graderstate_string, cfg, debug=args.verbose, markdown=args.markdown ) 
        print( "== Output of runAnswer ==" )
        print( r )
    else:
        r = testProgram( prob, ans, lit, criteria, graderstate_string, cfg, debug=args.verbose, mode=mode, markdown=args.markdown, outfile=args.outfile )
        print( r )
