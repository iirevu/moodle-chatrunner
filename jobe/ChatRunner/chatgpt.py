# (C) 2025: Jonas Julius Harang, Hans Georg Schaathun <hasc@ntnu.no>

# This should be copied into the CodeRunner question.

from ChatRunner.sandbox import runAnswer
import json

# Inputs from Moodle
qid = {{ QUESTION.questionid }}

studans = """{{STUDENT_ANSWER | e('py') }}"""
studansraw = """{{ STUDENT_ANSWER | raw }}"""

graderstate_string = "{{ QUESTION.stepinfo.graderstate| json_encode | e('py')}}"

sandboxparams = {
        "model" : "{{ model }}",
        "API" : "{{ API }}",
        "url" : "{{ url }}",
        "OPENAI_API_KEY" : "{{ OPENAI_API_KEY }}"
        }

# Load the problem text
with open('problem.md', 'r') as file:
    problem = file.read()
with open('literature.json', 'r') as file:
    literatur = json.load(file)

print( runAnswer( problem, studans, literatur, graderstate_string, sandboxparams, qid ) )
