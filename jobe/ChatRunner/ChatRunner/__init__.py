# (C) 2025: Hans Georg Schaathun <hasc@ntnu.no>

"""
ChatRunner manages quiz questions with automated grading by an LLM.

It is intended for use from CodeRunner in Moodle, but can also be
run in batch to test feedback quality of LLMs.
"""

from .query import queryAI
