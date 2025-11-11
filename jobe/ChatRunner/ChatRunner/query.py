# (C) 2025: Jonas Julius Harang, Hans Georg Schaathun <hasc@ntnu.no>

"""
Module handling the correspondence with the large language model LLM.

It defines the `Test` class which represents an individual test defined
by the LLM, as well as the query routine `queryAI()`.  Other definitions
should be considered internal.
"""

import requests, re, json

def queryAI(sandbox, ans, prompt, debug=False ):
   """
   Query the languagemodel.  It retunrs a list of `Test` objects.
   """
   response = chatRequest(sandbox, ans, prompt )

   status = response.status_code 
   if status != 200:
       print( response )
       raise Exception( f"HTTP requests returns {status}." )

   svar = extractAnswer(response, sandbox, debug=debug)

   r = [ dumpSvardata( svar ) ]
   r.extend( dumpResponse( svar ) )
   return r

def dumpSvardata(svar):
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
    testResults = []
    svar_fetched = formatAnswer(svar)

    if debug:
       print( "svar_fetched" )
       print( svar_fetched )
    testlist = json.loads(svar_fetched)

    return [ makeTest(test) for test in testlist ]

def extractAnswer(response,sandbox={},debug=False):
    """
    Extract the answer from the AI response.
    Returns the raw message contants from AI
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

def formatAnswer(svar,debug=False):
    """Format the raw result produced by `extractAnswer()`"""
    try:
       svar_fetched = re.search(r"\[.*\]", svar, flags=re.DOTALL).group(0)
    except Exception as e:
        print( "svar (crash):", svar )
        raise e
    if debug:
        print( "== fetched ==" )
        print(svar_fetched)
    return svar_fetched

def chatRequest(sandbox,prompt,ans):
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
    data = { 
             "model": sandbox.get( 'model', "gpt-4o" ),
             "format" : "json",
             "stream" : False,
             "messages": [ { "role": "assistant", "content": prompt },
                         { "role": "user", "content": ans } ]
           }
    return requests.post(openai_url, headers=headers, json=data)

class Test:
   """
   A `Test` object represents a single test assessed by the AI.
   It is used as the main constituent element in the `TestResults`
   class.
   """
   def __init__(self, testName=None):
      self.result = {"name": testName, "passed": False}

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

   def __str__(self):
      return json.dumps(self.result, indent=4)

   def __repr__(self):
      return json.dumps({"Testobject": self.result})

   def load(self, str_repr):
      try:
         obj = json.loads(str_repr)
         self.result = obj["Testobject"]
         return True
      except:
         return False

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

