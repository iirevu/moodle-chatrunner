# (C) 2025: Jonas Julius Harang, Hans Georg Schaathun <hasc@ntnu.no>

"""
Module handling the correspondence with the large language model LLM.

It defines the `Test` class which represents an individual test defined
by the LLM, as well as the query routine `queryAI()`.  Other definitions
should be considered internal.
"""

import requests, re, json
from .helper import getfn

def queryAI(sandbox, prompt, ans=None, debug=False ):
   """
   Query the languagemodel.  It retunrs a list of `Test` objects.

   It has two different modes.  If `ans=None`, the `prompt` should be
   a list of role/content objects, including a system prompt and the
   conversation history from the graderstate.

   Otherwise, `prompt` should be a template text for the system prompt
   and `ans` should be just the last student answer.
   """

   if ans is None:
       if not isinstance( prompt, list ):
          raise Exception( "Prompt should be a list of LLM messages." )
   else:
       if not isinstance( ans, str ):
           raise Exception( "Student answer should be string." )
       if not isinstance( prompt, str ):
           raise Exception( "Prompt should be string." )

   response = chatRequest(sandbox, prompt, ans, debug=debug )

   status = response.status_code 
   if status != 200:
       print( response )
       print( response.content )
       raise Exception( f"HTTP requests returns {status}." )

   svar = extractAnswer(response, sandbox, debug=debug)
   if debug:
       print( "queryAI() svar:", type(svar) )
       print( svar )

   r = [ dumpSvardata( svar ) ]
   r.extend( dumpResponse( svar ) )
   return r

def dumpSvardata(svar):
    """
    Create a Test object containing the feedback from LLM.
    """
    svardata = Test(testName="svardata")
    svardata.addResult("gpt_svar", json.dumps(svar))
    return svardata
def makeTest(test):
    try:
        ob = Test(testName=test.get( "testName", "Unnamed test" ))
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

def extractAnswer(response,sandbox={},debug=False):
    """
    Extract the message content from the AI response.

    It considers the API given by the sandbox, and handles OpenAI 
    and Ollama differently.

    Returns a string representing a JSON list, where each element
    is an object representing a test as created by the LLM.
    """
    api = sandbox.get( "API", "ollama" ).lower()
    svar = response.json()
    if api in [ "openai", "openapi" ]:
       svar = svar["choices"][0]
       if debug: print( "== Using OpenAPI" )
    if debug:
        print( "== complete «svar» from AI ==" )
        print(svar)
    svar = svar["message"]["content"]
    if debug:
       print( "== message content from AI ==" )
       print(svar)
    return svar


def chatRequest(sandbox,prompt,ans=None,debug=False):
    """
    Make the request to the LLM, using connection parameters
    from sandbox, and the given prompt and student answer ans.
    The return value is that produced by requests.request().
    """
    if sandbox is None:
        sandbox = {}
    openai_url = sandbox.get("url", "https://api.openai.com/v1/chat/completions")
    headers = { "Content-Type": "application/json" }
    if 'OPENAI_API_KEY' in sandbox:
         headers["Authorization"] = f"Bearer {sandbox['OPENAI_API_KEY']}"
    if ans is not None:
        if not isinstance( ans, str ):
            raise Exception( f"Student answer should be a string, not {type(ans)}." )
        msg = [ { "role": "system", "content": prompt },
                { "role": "user", "content": ans } ]
    else:
        if not isinstance( prompt, list ):
            raise Exception( f"Prompt should be a dict, not {type(prompt)}." )
        msg = prompt
    data = { 
             "model": sandbox.get( 'model', "gpt-4o" ),
             "format" : "json",
             "stream" : False,
             "messages": msg,
           }
    if ans is None:
        with open(getfn("schema.json"), 'r') as file:
            schema = json.load( file )
            data["response_format"] = { "type": "json_schema", "json_schema": schema } 
    if debug:
        print( json.dumps( data, indent=2 ) )
    return requests.post(openai_url, headers=headers, json=data)

class Test:
   """
   A `Test` object represents a single test assessed by the AI.
   It is used as the main constituent element in the `TestResults`
   class.

   A `Test` may also contain the raw response from the LLM, in which
   case it hqas name «gpt_svar».
   """
   def __init__(self, testName=None, content=None):
      self.result = {"name": testName, "passed": False}
      if content:
          self.load( content )

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
      return json.dumps({"Testobject": self.result}, indent=4)

   def load(self, str_repr):
      try:
         obj = json.loads(str_repr)
         self.result = obj["Testobject"]
      except:
         self.result = {
                 "name" : "nontest",
                 "type" : "nontest",
                 "content" : str_repr
                 }
      print( self )

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

