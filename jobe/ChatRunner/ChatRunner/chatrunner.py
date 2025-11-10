# (C) 2025: Jonas Julius Harang, Hans Georg Schaathun <hasc@ntnu.no>

"""
This is the main library, defining the classes and auxiliary
function for ChatRunner.
"""

import subprocess, base64, json, re, os
from .query import Test, queryAI


class TestResults:
   def __init__(self, output, exitCode=0, name=None, debug=False):
      """
      output: Output fra testprogram
      exitCode: 0: OK, 1: Feil/kræsj, 2: timeout, -1: Ingen tester å kjøre, -2: Testnummer finnes ikke
      name: this is never used in practice
      """
      self.testresults = []
      self.output = output
      self.other_output = ""
      self.exitCode = exitCode
      self.frac = 0
      self.name = name
      self.tableHeader = None
      self.tableRemap = None
      self.resultstable = None
      if exitCode != 0:
         self.results = { "failed":
              { "description": "CodeTester ran without loaded tests" } }
         return

      test = Test()
      for line in output.splitlines():
         if test.load(line):
            self.testresults.append(test)
            test = Test()
         else:
            self.other_output += line + "\n"
      self.numTests = len(self.testresults)
      self.debug = debug

   def finalise(self,debug=False):
      """
      Finalise the TestResults object, running makeResultTable()
      and mark().
      """
      if debug:
          print( "=== testResults ===" )
          print( self.contents() )

      tableRemap = {"iscorrect": "passed",
                  "Test": "name",
                  "Beskrivelse": "description"}
      tableHeader = ["iscorrect", "Test", "Beskrivelse"]
    
      self.makeResultTable(tableHeader,tableRemap)
      self.mark()
      if debug:
          print( "=== testResults (marked) ===" )
          print( self.contents() )
      # Format results
      return self
   def makeResultTable(self, tableHeader, tableRemap):
      """
      This function creates the `resultstable` attribute by
      formatting the test results
      """
      self.tableHeader = tableHeader
      self.resultstable = [tableHeader]

      if not tableRemap:
         tableRemap = {k:k for k in tableHeader}
      else:
         for header in tableHeader:
            if header not in tableRemap.keys():
               tableRemap.update({header:header})

      self.tableRemap = tableRemap
      i = 1
      for test in self.testresults:
         if self.debug:
            print( f"> test {i}" )
            print(test)
         i += 1

         row = []
         for column in self.tableHeader:
            try:
               row.append(test.result[tableRemap[column]])
            except:
               row = []
               break
         if self.debug: print( i, row )
         if row != []:
            self.resultstable.append(row)

   def contents(self):
      """
      Return the contents of the TestResults as a dictionary.
      """
      return  { "TestResultsObj": {
            "testresults": self.testresults,
            "other_output": self.other_output,
            "tableHeader": self.tableHeader,
            "tableRemap": self.tableRemap,
            "resultstable": self.resultstable,
            "frac": self.frac,
            "name": self.name
         }
      }
   def __repr__(self):
      """
      Return the contents of the TestResults as a string.
      """
      contents = self.contents()
      contents["testresults"] = [ t.dump() for t in contents["testresults"] ]
      return json.dumps(contents)

   def dump(self):
      """
      Return the contents of the TestResults as a string.
      """
      return self.__repr__()

   def load(self, str_repr):
      obj_read = False
      self.unencoded = ""
      for line in str_repr:
         try:
            data = json.loads(line)
            obj = data["TestResultsObj"]
            self.testresults = [Test() for res in obj["testresults"]]
            self.testresults = list(map(Test.load, self.testresults))
            self.other_output = obj["other_output"]
            self.tableHeader = obj["tableHeader"]
            self.tableRemap = obj["tableRemap"]
            self.resultstable = obj["resultstable"]
            self.frac = obj["frac"]
            self.name = obj["name"]
            obj_read = True
         except:
            self.unencoded += line + '\n'
      return obj_read

   def mark(self):
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

   def getCodeRunnerResult(self,
                           prehtml=None,
                           graderstate=None,
                           other_lines=False ):
       """
       Return the test results as a dict suitable for JSON export
       in the format used by CodeRunner.
       """
       if other_lines:
         prehtml = f"""<h2> Other output / error-messages from testgrader </h2>
         <p><br>
         """ + self.other_output.replace("\n", "<br>") + """
         </p></br>"""
       obj = { "fraction": self.frac,
               "testresults": self.resultstable,
               "prologuehtml": prehtml,
               "epiloguehtml": self.phtml(),
               "graderstate": graderstate }
       return obj
   def getCodeRunnerOutput(self,
                           prehtml=None,
                           graderstate=None,
                           other_lines=False ):
       """
       Return the test results as used by CodeRunner.
       This is string representation of a JSON object.
       """
       obj = self.getCodeRunnerResult(
               prehtml,graderstate,other_lines)
       return json.dumps( obj, ensure_ascii=False )
   def mergeResults(self, merging_result):
      if self.resultstable == None:
         if merging_result.resultstable == None:
            pass
         else:
            self.resultstable=merging_result.resultstable
            self.tableHeader = merging_result.tableHeader
            self.tableRemap = merging_result.tableRemap
      elif merging_result.resultstable == None:
         pass
      else:
         self.resultstable = self.resultstable + merging_result.resultstable[1:]

      self.other_output += merging_result.other_output
      self.testresults = self.testresults+merging_result.testresults
   def phtml(self):
       rl = [ test.formatResult() for test in self.testresults ]
       rl = [ x for x in rl if x is not None ]
       return "\n".join( rl )

def getfn(fn):
    dir = os.path.dirname(os.path.abspath(__file__))
    return( os.path.join( dir, fn ) )


def runTest(prg, timeout=1.0):
      """
      Run the test program as a supprocess catching exceotions.  
      It produces a `TestResults` object, incorporating the test results,
      or appropriate error codes if the program fails.
      """

      try:
         with open("code.py", "w") as fout:
             fout.write( prg )
         sp = subprocess.run(['python3', 'code.py'],
             stderr = subprocess.STDOUT,
             universal_newlines=False,
             timeout=timeout,
             stdout=subprocess.PIPE )
         output = sp.stdout.decode()
         return TestResults(output)
      except subprocess.CalledProcessError as e:
         output = e.stdout.decode()
         return TestResults(output, exitCode=1)
      except subprocess.TimeoutExpired as e:
         output = e.stdout
         if output:
            output= output.decode()
         else:
             output = "Ingen output fra testprogrammet"
         return TestResults(output, exitCode=2)

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

def loadtestprogram(ans,problem,literatur,gs,sandbox={},
                    pyfn="testprogram.py.txt",mdfn="prompt.md"):
    dir = os.path.dirname(os.path.abspath(__file__))
    mdfn = os.path.join( dir, mdfn )
    pyfn = os.path.join( dir, pyfn )

    prompt = getPrompt(problem,literatur,gs,mdfn=mdfn)

    with open(pyfn, 'r') as file:
        prg = file.read()
    return prg.format( prompt=prompt, studans=ans, sandbox=sandbox )

def getGraderstate(gs,studans):
    # Interpret graderstate
    step = 0
    if (not gs in ['null', '""', "''", '', '[]']):
       graderstate = json.loads(gs)
       step = graderstate["step"]
       graderstate["studans"].append(studans)
    else:
       graderstate = {"step": 0, "studans": [studans], "svar": []}
    return graderstate

def advanceGraderstate(gs,res,debug=False):
    """
    Advance the graderstate, adding the response from the AI.
    """
    i = 1
    for test in res.testresults:
       if test.result["name"] == "svardata":
          gs["svar"].append(test.result["gpt_svar"])
       if debug:
         print( f"=> test {i}" )
         print(test)
         i += 1

    gs["step"] += 1

def runAnswer(problem,studans,literatur={},gs="",sandbox=None,qid=0,debug=False,subproc=True):
    """
    Run the CodeGrader, with pre- and post-processing of data.
    """

    if sandbox is None:
        raise Exception( "No sandbox received by runAnswer." )

    graderstate = getGraderstate(gs,studans)

    test_program = loadtestprogram(
            studans,
            problem,
            literatur,
            graderstate,
            sandbox=sandbox,
            pyfn="testprogram.py.txt",
            mdfn="prompt.md")

    testResults = runTest( test_program, timeout=40.0)
    testResults.finalise(debug=debug)

    advanceGraderstate( graderstate, testResults, debug=debug )

    # Format feedback for display
    if debug:
        print( "=runAnswer in debug mode=" )
        return testResults.getCodeRunnerResult(
          other_lines=True,
          graderstate=graderstate)
    else:
       return testResults.getCodeRunnerOutput(
          other_lines=True,
          graderstate=graderstate)

def testProgram(problem,studans,literatur={},gs="",sandbox={},qid=0,debug=False):
    """
    This function is supposed to be functionally identical to
    `runAnswer()` without using the sandbox.  The code from 
    the test program is integrated, with additional debug output.

    In general, this function should be used to test the functionality 
    and the language models from the command line.
    """

    graderstate = getGraderstate(gs,studans)
    prompt = getPrompt(problem,literatur,gs)

    testResults = queryAI(sandbox, studans, prompt, debug=debug)

    if debug:
       i = 1
       for test in testResults:
          print( f"==== test {i} ====" )
          print(test)
          i += 1

    # Dump the result as a string and have `TestResults` reparse it,
    # in the way that is required for `subprocess` in `runAnswer()`.
    output = "\n".join( [ x.dump() for x in testResults ] )
    testResults = TestResults(output)
    testResults.finalise()

    advanceGraderstate( graderstate, testResults, debug=debug )

    # Format feedback for display
    return testResults.getCodeRunnerResult(
        other_lines=True,
        graderstate=graderstate)

