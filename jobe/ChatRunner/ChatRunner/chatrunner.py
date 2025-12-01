# (C) 2025: Jonas Julius Harang, Hans Georg Schaathun <hasc@ntnu.no>

"""
This is the main library, defining the classes and auxiliary
function for ChatRunner.
"""

import subprocess, base64, json, os
from .query import Test, queryAI

class Table:
    """Representation of a table with header and a list of rows.
    It provides rendering in Markdown."""
    def __init__(self,lst,header):
        self.header = header
        self.contents = lst
    def __iter__(self):
        return self.asList().__iter__()
    def asList(self):
        """
        Return the table and header as a list of list.
        This is used for string dumps in other classes.
        """
        lst = [ self.header ] + self.contents
        return lst
    def markdown(self):
        """Render the table in Markdown.  Returns a string."""
        h = "| " +  " | ".join( self.header ) + " |\n"
        sep = "| " +  " | ".join( [ " :- " for _ in self.header ] ) + " |\n"
        l = [  "| " +  " | ".join( map(str,x) ) + " |" for x in self.contents ]
        return h + sep + "\n".join( l )

def parseTestResults(output):
      testresults = []
      other_output = []
      test = Test()
      for line in output.splitlines():
         if test.load(line):
            testresults.append(test)
            test = Test()
         else:
            other_output.append( line )
      return testresults, other_output
class TestResults:
   """Representation of the complete assessment result.
   This includes a list of `Test` objects, representing individual test
   criteria as determined by the AI model.

   Output which cannot be represented as `Test` objects are provided
   in as `other_output`.

   The results table (`Table` object) is formatted from the `Test` objects.
   A grade (`frac`) is calculated as the fraction of passed tests.
   """
   def __init__(self, output=None, ob=None, exitCode=0, debug=False):
      """
      output: Output fra testprogram
      exitCode: 0: OK, 1: Feil/kræsj, 2: timeout, -1: Ingen tester å kjøre, -2: Testnummer finnes ikke
      name: this is never used in practice
      """
      self.output = output
      self.exitCode = exitCode
      self.frac = 0
      self.tableHeader = None
      self.resultstable = None
      self.debug = debug

      if exitCode != 0:
         self.results = { "failed":
              { "description": "CodeTester ran without loaded tests" } }
         self.testresults = None
      if output is not None:
          if ob is not None:
              raise Exception( "Either output or ob should be given, not both." )
          self.testresults, self.other_output = parseTestResults(output)
      elif ob is not None:
          self.testresults = ob
          self.other_output = []
      else:
          raise Exception( "Either output or ob should be given." )

      self.numTests = len(self.testresults)

   def debugPrintResults(self): return debugPrintResults(self.testresults)
   def finalise(self,debug=False):
      """
      Finalise the TestResults object, running makeResultTable()
      and mark().
      """

      tableHeader = ["iscorrect", "Test", "Beskrivelse"]
    
      self.makeResultTable( tableHeader )
      self.mark()
      if debug:
          print( "=== testResults (marked) ===" )
          print( self.getMarkdownResult() )
      # Format results
      return self

   def makeResultTable( self, tableHeader ):
      """
      This function creates the `resultstable` attribute by
      formatting the test results
      """
      self.tableHeader = tableHeader
      resultstable = []

      tableRemap = {"iscorrect": "passed",
                  "Test": "name",
                  "Beskrivelse": "description"}

      for header in tableHeader:
          if header not in tableRemap.keys():
              tableRemap.update({header:header})

      # self.tableRemap = tableRemap
      if self.debug: self.debugPrintResults()

      for test in self.testresults:
         row = []
         for column in self.tableHeader:
            try:
               row.append(test.result[tableRemap[column]])
            except:
               row = []
               break
         if self.debug: print( i, row )
         if row != []:
            resultstable.append(row)

      self.resultstable = Table(resultstable,tableHeader)
   def __repr__(self):
      """
      Return the contents of the TestResults as a string.
      """
      contents = { "TestResultsObj": {
            "testresults": [ t.dump() for t in self.testresults ],
            "other_output": "\n".join(self.other_output),
            "tableHeader": self.tableHeader,
            "resultstable": self.resultstable.asList(),
            "frac": self.frac
         }
      }
      return json.dumps(contents)

   def mark(self):
      """Compute the grade `frac` from the testResult."""
      total_marks = 0
      obtained_marks = 0
      for test in self.testresults:
         if "mark" in test.result.keys():
            mark = test.result["mark"]
            total_marks += mark
         else:
            mark = 0
         if test.result["passed"]:
            obtained_marks += mark
      if total_marks != 0:
         self.frac = obtained_marks/total_marks
      else:
         self.frac = 0

   def getMarkdownResult(self,
                           prehtml=None,
                           graderstate=None,
                           other_lines=False ):
       if other_lines:
         prehtml = ( "# Other output / error-messages from testgrader\n\n" 
                 + "\n".join(self.other_output) + "\n" )
       else: prehtml = ""
       if graderstate:
           gs = "# Graderstate\n" + json.dumps( graderstate )
           gs += "\n\n"
       else:
           gs = ""
       tab = "# Results table\n\n" + self.resultstable.markdown()
       header = "# Assessment output\n\n"
       return gs + header + prehtml + tab + "\n\n" + self.pmd() + f"\nFraction: {self.frac}\n"
   def getCodeRunnerOutput(self,
                           prehtml=None,
                           graderstate=None,
                           other_lines=False ):
       """
       Return the test results as used by CodeRunner.
       This is string representation of a JSON object.
       """
       if other_lines:
         prehtml = f"""<h2> Other output / error-messages from testgrader </h2>
         <p><br>
         """ + "<br>".join( self.other_output ) + """
         </p></br>"""
       obj = { "fraction": self.frac,
               "testresults": self.resultstable.asList(),
               "prologuehtml": prehtml,
               "epiloguehtml": self.phtml(),
               "graderstate": graderstate }
       return json.dumps( obj, ensure_ascii=False )

   def phtml(self):
       rl = [ test.formatResult() for test in self.testresults ]
       rl = [ x for x in rl if x is not None ]
       return "\n".join( rl )
   def pmd(self):
       rl = [ test.formatMarkdown() for test in self.testresults ]
       rl = [ x for x in rl if x is not None ]
       return "\n".join( rl )
def debugPrintResults(testResults):
    """Print a list of Test objects for debugging purposes."""
    i = 1
    for test in testResults:
        print( f"==== test {i} ====" )
        print(test)
        i += 1

def getfn(fn):
    dir = os.path.dirname(os.path.abspath(__file__))
    return( os.path.join( dir, fn ) )



def getPrompt(problem,literatur,gs,mdfn=getfn("prompt.md")):
    try:
       prevans = gs[ "studans" ][-1]
    except:
       prevans = "Ingen tidligere svar gitt"

    with open(mdfn, 'r') as file:
        prompt = file.read()
    prompt = prompt.format( problem=problem,
                            literatur=literatur,
                            prevans=prevans,
                           )
    return prompt

class GraderState:
    def __init__(self,gs="",studans=None):
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
    def __init__(self,problem,studans,literatur={},gs="",sandbox={},qid=0,debug=False):
        self.graderstate = GraderState(gs,studans)
        self.literatur = literatur
        self.studans = studans
        self.sandbox = sandbox
        self.debug = debug
        self.problem = problem
    def getPrompt(self,debug=None):
        return getPrompt(self.problem,self.literatur,self.graderstate)
    def getHistory(self,debug=None):
        return self.graderstate.getHistory()
    def queryAI(self,debug=None):
        if debug is None: debug = self.debug
        response = queryAI(self.sandbox, self.getPrompt(), self.studans, debug=debug)
        if debug: debugPrintResults(response)

        testResults = TestResults(ob=response)
        testResults.finalise()
        self.testResults = testResults
        return testResults
    def advanceGraderstate(self,debug=None):
        """
        Advance the graderstate, adding the response from the AI.
        """

        if debug is None: debug = self.debug

        res = self.testResults

        xs = [ test for test in res.testresults if test.result["name"] == "svardata" ]
        if len(xs) == 0:
            raise Exception( "No feedback" )
        if len(xs) > 1:
            raise Exception( "Multiple feedback entries" )
        self.graderstate.addFeedback(xs[0].result["gpt_svar"])
        return self.graderstate
    def getResult(self,debug=None):
        return self.testResults
    def getMarkdownResult(self,*arg,**kw):
        return self.testResults.getMarkdownResult(*arg,**kw,graderstate=self.graderstate)

class NewEngine(Engine):
    def getPrompt(self,debug=None):
        with open(mdfn, 'r') as file:
            template = file.read()
        sys = prompt.format( problem=problem, literatur=literatur )
        prompt = [ { "role" : "system",  "content" : sys } ]
        prompt.extend( self.getHistory() )
        return prompt

    def queryAI(self,debug=None):
        if debug is None: debug = self.debug
        response = queryAI(self.sandbox, self.getPrompt(), debug=debug)
        if debug: debugPrintResults(response)

        testResults = TestResults(ob=response)
        testResults.finalise()
        self.testResults = testResults
        return testResults

class DumpEngine(Engine):
    def queryAI(self,debug=None):
        if debug is None: debug = self.debug
        response = queryAI(self.sandbox, self.getPrompt(), self.studans, debug=debug)
        if debug: debugPrintResults(response)
        # Dump the result as a string and have `TestResults` reparse it,
        # in the way that is required for `subprocess` in `runAnswer()`.
        output = "\n".join( [ x.dump() for x in response ] )
        testResults = TestResults(output)
        testResults.finalise()
        self.testResults = testResults
        return testResults


def testProgram(problem,studans,literatur={},gs="",sandbox={},qid=0,debug=False,dumpmode=False, markdown=False, outfile=None):
    """
    This function is supposed to be functionally identical to
    `runAnswer()` without using the sandbox.  The code from 
    the test program is integrated, with additional debug output.

    In general, this function should be used to test the functionality 
    and the language models from the command line.
    """

    if dumpmode:
       eng = DumpEngine(problem,studans,literatur,gs,sandbox,qid,debug)
    else:
       eng = Engine(problem,studans,literatur,gs,sandbox,qid,debug)
    testResults = eng.queryAI()
    if debug: testResults.debugPrintResults()
    eng.advanceGraderstate( )
    if outfile:
        with open(outfile, 'w') as f:
             json.dump(eng.getResult(), f, indent=4) 
    if markdown:
       return eng.getMarkdownResult( other_lines=True )
    else:
       return eng.getResult().getCodeRunnerOutput( other_lines=True )
