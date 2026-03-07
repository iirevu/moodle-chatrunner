# (C) 2025: Jonas Julius Harang, Hans Georg Schaathun <hasc@ntnu.no>

"""
This is the main library, defining the engine classes and auxiliary
function for ChatRunner.

The `Engine` class is the main API to manage queries to the LLM.
Different subclasses exist,
+ `Engine` uses the original, naive prompt 
+ `NewEngine` makes better use of the API
+ `DumpEngine` tests the reparsing required in the sandbox
+ `SandboxEngine` (from `sandbox` module) tests the sandbox required
  by `CodeRunner` in Moodle.
"""

import subprocess, base64, json, os
from .query import queryAI
from .helper import getfn

from .TestResults import Table, TestResults, Test

from typing import List

class GraderState:
    """The GraderState class wraps a graderstate object from Moodle.
    The constructor parses JSON from a string or creates an empty
    graderstate if empty, and other methods support updating the state.  
    """
    def __init__(self,gs="",studans=None):
        """Parse the graderstrate from the string `gs` and add the student
        answer if given.
        """
        if isinstance( gs, dict ):
            self.graderstate = gs
        elif not isinstance( gs, str ):
            raise Exception("GraderState should be string or dict.")
        elif (not gs in ['null', '""', "''", '', '[]']):
            self.graderstate = json.loads(gs)
        else:
            self.graderstate = {"step": 0, "studans": [], "svar": []}
        step = self.graderstate["step"]
        nans = len(self.graderstate["studans"]) 
        nfb = len(self.graderstate["svar"]) 
        if nans != step:
           raise Exception(
             f"Wrong number of student answers ({nans} ansers at step {step}.")
        if nfb != step:
           raise Exception(
             f"Wrong number of feedback items ({nfb} at step {step}.")
        if studans is not None:
           self.addAnswer(studans)
    def json(self):
       return json.dumps( self.graderstate )
    def __str__(self):
       return json.dumps( self.graderstate, indent=2 )
    def __repr__(self):
       return json.dumps( self.graderstate, indent=2 )
    def addAnswer(self,studans):
       self.graderstate["studans"].append(studans)
    def addFeedback(self,svar):
       self.graderstate["svar"].append(svar)
       self.graderstate["step"] += 1
    def getHistory(self,debug=None):
        """Return the feedback history as a conversation for OpenAI API."""
        gs = self.graderstate
        ans = [ { "role": "user", "content": x } for x in gs["studans"] ]
        res = [ { "role": "assistant", "content": x } for x in gs["svar"] ]
        if len(ans) != len(res) + 1:
                raise Exception("Should have had feedback for all but last student answer")
        r = ans + res
        r[::2] = ans
        r[1::2] = res
        return r

class Engine:
    """
    The Engine class provides the API to process student responses
    and get feedback from an LLM.  
    """
    def __init__(self,problem,studans=None,
                 literatur={},criteria="",gs="",sandbox={},qid=0,
                 debug=False):
        print( "[Engine] init - debug mode" )
        if studans is None:
            raise Exception("Not implemented")
        else:
            self.problem = problem
            self.studans = studans
            self.criteria = criteria
        self.graderstate = GraderState(gs,studans)
        self.literatur = literatur
        self.sandbox = sandbox
        self.debug = debug
    def getPrompt(self,debug=None):
        gs = self.graderstate
        mdfn=getfn("prompt.md")
        try:
           prevans = gs[ "studans" ][-1]
        except:
           prevans = "Ingen tidligere svar gitt"

        with open(mdfn, 'r') as file:
            prompt = file.read()
        prompt = prompt.format( problem=self.problem,
                            literatur=self.literatur,
                            prevans=prevans,
                           )
        return prompt
    def getHistory(self,debug=None):
        return self.graderstate.getHistory()
    def getGraderState(self,debug=None):
        return self.graderstate
    def queryAI(self,debug=None):
        if debug is None: debug = self.debug
        prompt = self.getPrompt()
        testResults = queryAI(self.sandbox, prompt, self.studans, debug=debug)
        if debug: 
            print( "== prompt ==" )
            print( prompt )
            print( "== END prompt ==" )
            testResults.debugPrintResults()

        testResults.finalise()
        self.testResults = testResults
        return testResults
    def advanceGraderstate(self,debug=None):
        """
        Advance the graderstate, adding the raw response from the AI.
        """
        res = self.testResults
        self.graderstate.addFeedback( res.getRawResponse() )
        return self.graderstate
    def getResult(self,debug=None):
        return self.testResults
    def getMarkdownResult(self,*arg,**kw):
        return self.testResults.getMarkdownResult(*arg,**kw,graderstate=self.graderstate)

class NewEngine(Engine):
    def getPrompt(self,mdfn=getfn("prompt2.md"),debug=None):
        if debug is None: debug = self.debug
        with open(mdfn, 'r') as file:
            template = file.read()
        print( f"[getPrompt] mdfn={mdfn}" )
        sys = template.format( problem=self.problem
                             , criteria=self.criteria
                             , literatur=self.literatur )
        prompt = [ { "role" : "system",  "content" : sys } ]
        prompt.extend( self.getHistory() )
        return prompt

    def queryAI(self,debug=None):
        if debug is None: debug = self.debug
        testResults = queryAI(self.sandbox, self.getPrompt(), debug=debug)
        if debug: response.debugPrintResults()

        testResults.finalise()
        self.testResults = testResults
        return testResults

class DumpEngine(Engine):
    """DumpEngine tests the extra step of dumping and reparsing
    the response, as is required with the `SandboxEngine` but
    without using the sandbox (subprocess).
    """
    def queryAI(self,debug=None):
        if debug is None: debug = self.debug
        response = queryAI(self.sandbox, self.getPrompt(), self.studans, debug=debug)
        if debug: response.debugPrintResults()

        # Dump the result as a string and have `TestResults` reparse it,
        # in the way that is required for `subprocess` in `runAnswer()`.
        output = response.dump()
        testResults = TestResults(output,debug=debug)
        testResults.finalise()
        self.testResults = testResults
        return testResults


def testProgram(problem,studans,literatur={},criteria="",gs="",sandbox={},qid=0,
                debug=False,mode="baseline", markdown=False, outfile=None, raw=False):
    """
    This function is supposed to be functionally identical to
    `runAnswer()` without using the sandbox.  The code from 
    the test program is integrated, with additional debug output.

    In general, this function should be used to test the functionality 
    and the language models from the command line.
    """

    if debug:
        print( f"[testProgram] debug; mode={mode}." )

    if mode == "baseline":
       eng = Engine(problem,studans,literatur,criteria,gs,sandbox,qid,debug)
    elif mode == "new":
        eng = NewEngine(problem,studans,literatur,criteria,gs,sandbox,qid,debug)
    elif mode == "dump":
        eng = DumpEngine(problem,studans,literatur,criteria,gs,sandbox,qid,debug)
    else:
        raise Exception( f"Unknown mode {mode}." )
    testResults = eng.queryAI()
    if debug: testResults.debugPrintResults()
    eng.advanceGraderstate( )
    if debug: print( eng.getGraderState() )
    if outfile:
        with open(outfile, 'w') as f:
            tr = eng.getResult().asdict()
            json.dump(tr, f, indent=4) 
    if raw:
       return eng.getResult()
    elif markdown:
       return eng.getMarkdownResult( )
    else:
       return eng.getResult().getCodeRunnerOutput( other_lines=True )
