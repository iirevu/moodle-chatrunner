# (C) 2025: Jonas Julius Harang, Hans Georg Schaathun <hasc@ntnu.no>

"""
Module handling the correspondence with the large language model LLM.

The only function intended for export is `queryAI()`.
Other definitions should be considered internal.
"""

import requests, json
from .helper import getfn
from .TestResults import TestResults, Test

def queryAI(sandbox, prompt, ans=None, debug=False ):
   """
   Query the languagemodel.  It returns a list of `Test` objects.

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

   return TestResults( raw=svar )

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

