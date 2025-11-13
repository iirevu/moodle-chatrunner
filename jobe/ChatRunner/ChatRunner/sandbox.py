from .chatrunner import *

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

def loadtestprogram(ans,prompt,sandbox={},
                    pyfn="testprogram.py.txt",mdfn="prompt.md"):
    dir = os.path.dirname(os.path.abspath(__file__))
    mdfn = os.path.join( dir, mdfn )
    pyfn = os.path.join( dir, pyfn )

    with open(pyfn, 'r') as file:
        prg = file.read()
    return prg.format( prompt=prompt, studans=ans, sandbox=sandbox )

class SandboxEngine(Engine):
    def queryAI(self,debug=None):
        if debug is None: debug = self.debug
        test_program = loadtestprogram(
            self.studans,
            self.prompt,
            sandbox=self.sandbox,
            pyfn="testprogram.py.txt",
            mdfn="prompt.md")

        testResults = runTest( test_program, timeout=40.0)
        testResults.finalise()

        self.testResults = testResults
        return testResults

def runAnswer(problem,studans,literatur={},gs="",sandbox=None,qid=0,debug=False,subproc=True):
    """
    Run the CodeGrader in a sandbox, with pre- and post-processing of data.
    """

    if sandbox is None:
        raise Exception( "No sandbox received by runAnswer." )

    eng = SandboxEngine(problem,studans,literatur,gs,sandbox,qid,debug)
    testResults = eng.queryAI()
    if debug: testResults.debugPrintResults()
    eng.advanceGraderstate( )
    return eng.getMarkdownResult( other_lines=True )

    # Format feedback for display
    if debug:
        print( "== runAnswer in debug mode ==" )
        return eng.getMarkdownResult( other_lines=True )
    else:
       return eng.getCodeRunnerOutput( other_lines=True )
