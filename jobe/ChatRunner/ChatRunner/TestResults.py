# (C) 2025-26: Jonas Julius Harang, Hans Georg Schaathun <hasc@ntnu.no>

from typing import List
import re, json

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

class Test:
   """
   A `Test` object represents a single test assessed by the AI.
   It is used as the main constituent element in the `TestResults`
   class.

   A `Test` may also contain the raw response from the LLM, in which
   case it has name «gpt_svar».
   """
   def __init__(self, testName=None, content=None, type="test"):
      if content:
          self.result = content
      else:
          self.result = {"name": testName, "passed": False, "type" : type }

   def addResult(self, field_name, field_data):
      """
      Add resultdata. Data has a key (field_name) and value (field_data)
      """
      self.result.update({field_name: field_data})

   def addResults(self, res_dict):
      for k, v in res_dict.items():
         self.addResult(k,v)

   def pass_test(self, passed):
      self.result["passed"] = passed
   def testType(self):
       return self.result.get("type","test")

   def asdict(self):
      return self.result
   def __str__(self):
      return json.dumps(self.result, indent=4)

   def __repr__(self):
      return json.dumps({"Test": self.result}, indent=4)

   def isTest(self):
       """
       Returns true if the object is a well-formed test, as opposed to containers
       for raw LLM output or malformed output.
       """
       return self.testType() == "test"
   def dump(self):
      return self.__repr__()
   def formatMarkdown(self):
      """Return a string presenting the test result in Markdown."""
      result = self.result
      feedback = False
      if result["passed"]:
          header = f'## Passed: {result["name"]}\n'
      elif "resultat" in result.keys():
          header = f'## Failed: {result["name"]}\n'
      else: return None
      return ( header + f'\n{result["resultat"]}\n' )
   def formatResult(self):
      """Return a string presenting the test result in HTML."""
      result = self.result
      feedback = False
      if result["passed"]:
            color = "Lime"
      elif "resultat" in result.keys():
            color = "Red"
      else: return None
      return ( f'<h2 style="background-color:{color};">{result["name"]}</h2>'
           + f'\n<p>{result["resultat"]} </p>' )


def dumpSvardata(svar):
    """
    Create a Test object containing the feedback from LLM.
    """
    svardata = Test(testName="Raw GPT Response",type="rawresponse")
    svardata.addResult("rawresponse", json.dumps(svar))
    svardata.addResult("type", "rawresponse")
    return svardata
def makeTest(test) -> Test:
    try:
        ob = Test(testName=test.get( "testName", "Unnamed test" ),type="test")
    except Exception as e:
        print(test)
        raise(e)
    ob.addResult("mark", 1)
    for k,v in test.items():
        if k == 'iscorrect':
            ob.pass_test(v)
        elif k == "testName":
            continue
        else:
            ob.addResult(k,v)
    return ob

def dumpResponse(svar,debug=False):
    """
    Parse JSON list from the LLM and create Test objects.
    """

    # Extract JSON list, stripping leading and trailing characters.
    try:
       svar_fetched = re.search(r"\[.*\]", svar, flags=re.DOTALL).group(0)
    except Exception as e:
        ob = Test(testName="No JSON list found in response string.")
        ob.addResult( "rawfeedback", svar )
        ob.addResult( "decodeerror", str(e) )
        ob.addResult( "type", "malformed" )
        if debug:
            print( ob )
        return [ ob ]

    # Parse the JSON string
    try:
       testlist = json.loads(svar_fetched,strict=False)
    except json.JSONDecodeError as e:
        ob = Test(testName="Malformed JSON result")
        ob.addResult( "rawfeedback", svar_fetched )
        ob.addResult( "decodeerror", str(e) )
        ob.addResult( "type", "malformed" )
        if debug:
            print( ob )
        return [ ob ]

    # Create Test objects and return
    return [ makeTest(test) for test in testlist ]


class TestResults:
   """Representation of the complete assessment result.
   This includes a list of `Test` objects, representing individual test
   criteria as determined by the AI model.

   Output which cannot be represented as `Test` objects are provided
   in as `other_output`.

   The results table (`Table` object) is formatted from the `Test` objects.
   A grade (`frac`) is calculated as the fraction of passed tests.
   """
   def __init__(self, output : str = None
                , raw : str = None
                , ob : List[Test] = None
                , exitCode : int = 0
                , debug : bool = False):
      """
      output: Output fra testprogram

      exitCode: 
      + 0: OK
      + 1: Feil/kræsj
      + 2: timeout
      + -1: Ingen tester å kjøre
      + -2: Testnummer finnes ikke

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
      if raw is not None:
          if not isinstance(raw,str):
              raise Exception( "TestResult() - raw data should be str." )
          self.rawresponse = dumpSvardata( raw )
          self.testresults = dumpResponse( raw )
      else:
          if output is not None:
              if not isinstance(output,str):
                  raise Exception( "TestResult() - output argument should be str." )
              if ob is not None:
                  raise Exception( 
                         "Either output or ob should be given, not both." )
              try:
                  ob = json.loads( output )
              except json.decoder.JSONDecodeError as e:
                  print( "[TestResults] JSON decode error" )
                  print( output )
                  raise e
          elif ob is None:
              raise Exception( "One of output, ob, or raw should be given." )
          try:
              self.rawresponse = Test( content=ob["rawresponse"] )
              self.testresults = [ Test(content=x) for x in ob["testresults"] ]
          except KeyError as e:
              print( "[TestResults] KeyError" )
              print( ob )
              raise e
      if debug:
          cnt = {}
          for test in self.testresults:
              try:
                  tp = test.result["type"]
              except KeyError as e:
                  print( test.result )
                  raise e
              cnt[tp] = cnt.get("tp",0) + 1
          print( cnt )
      self.numTests = len(self.testresults)

   def __iter__(self): return self.testresults.__iter__()
   def debugPrintResults(self): 
       """Print a list of Test objects for debugging purposes."""
       i = 1
       for test in self:
           print( f"==== test {i} ====" )
           print(test)
           i += 1
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

      idx = 1
      for test in self.testresults:
         row = []
         for column in self.tableHeader:
            try:
               row.append(test.result[tableRemap[column]])
            except:
               row = []
               break
         if self.debug: 
             print( idx, row )
             idx += 1
         if row != []:
            resultstable.append(row)

      self.resultstable = Table(resultstable,tableHeader)
   def getOtherOutput(self):
       return [ x.asdict() for x in self.testresults if not x.isTest() ]

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
         if "passed" not in test.result:
             print( 'No "passed" entry in test result.' )
             print( test.result )
         elif test.result["passed"]:
            obtained_marks += mark
      if total_marks != 0:
         self.frac = obtained_marks/total_marks
      else:
         self.frac = 0

   def getMarkdownResult(self, graderstate=None):
       ol = self.getOtherOutput()
       if ol:
           prehtml = ( "# Other output / error-messages from testgrader\n\n"
              + "\n".join(ol) + "\n" )
       else: prehtml = ""
       if graderstate:
           gs = "# Graderstate\n\n" + str(graderstate)
           gs += "\n\n"
       else:
           gs = ""
       tab = "# Results table\n\n" + self.resultstable.markdown()
       header = "# Assessment output\n\n"
       return gs + header + prehtml + tab + "\n\n" + self.pmd() + f"\nFraction: {self.frac}\n"
   def getFeedbackObject(self,
                           graderstate=None,
                           other_lines=False ):
       """
       Return the test results as a `dict`.
       """
       rl = [ test.asdict() for test in self.testresults ]
       rr = [ x for x in rl if x["type"] == "rawresponse" ]
       rl = [ x for x in rl if not "gpt_svar" in x.keys() ]
       ol = self.getOtherOutput()
       obj = { "fraction": self.frac,
               "testresults": self.resultstable.asList(),
               "rawresonse": rr[0],
               "otherfeedback": ol,
               "tableHeader": self.tableHeader,
               "testfeedback": rl }
       if graderstate:
           obj["graderstate"] = graderstate 
       return obj
   def __repr__(self):
      """
      Return the contents of the TestResults as a string.
      """
      return json.dumps( self.asdict() )
   def dump(self): return self.__repr__()
   def getCodeRunnerOutput(self,
                           graderstate=None,
                           other_lines=False ):
       """
       Return the test results as used by CodeRunner.
       This is string representation of a JSON object.
       """
       if other_lines:
          ol = self.getOtherOutput()
       else: ol = []
       if ol:
              prehtml = f"""<h2>Other output / error-messages from testgrader </h2>
         <p><br>
         {"<br>".join( ol )}
         </p></br>"""
       else: prehtml = ""
       obj = { "fraction": self.frac,
               "testresults": self.resultstable.asList(),
               "prologuehtml": prehtml,
               "epiloguehtml": self.phtml(),
               "graderstate": graderstate }
       return json.dumps( obj, ensure_ascii=False )

   def asdict(self):
       return {
         "rawresponse" : self.rawresponse.asdict(),
         "testresults" : [ x.asdict() for x in self.testresults ]
        }
   def phtml(self):
       """Return freeform feedback in HTML."""
       rl = [ test.formatResult() for test in self.testresults ]
       rl = [ x for x in rl if x is not None ]
       return "\n".join( rl )
   def pmd(self):
       """Return freeform feedback in Markdown."""
       rl = [ test.formatMarkdown() for test in self.testresults ]
       rl = [ x for x in rl if x is not None ]
       return "\n".join( rl )
   def getRawResponse(self,debug=None):
        rl = [ test.asdict() for test in self.testresults ]
        xs = [ x for x in rl if x["type"] == "rawresponse" ]
        if len(xs) == 0:
            print( self )
            raise Exception( "No raw response" )
        if len(xs) > 1:
            raise Exception( "Multiple raw response entries" )
        return( xs[0] )

