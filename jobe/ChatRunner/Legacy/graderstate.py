# (C) 2025: Jonas Julius Harang, Hans Georg Schaathun <hasc@ntnu.no>

"""
The GraderState class is supposed to provide pretty printing and replace
some auxiliary functions in chatrunner.  Work in progress.
"""


class GraderState:
    def __init__(self,gs,studans):
        step = 0
        if (not gs in ['null', '""', "''", '', '[]']):
           graderstate = json.loads(gs)
           step = graderstate["step"]
           graderstate["studans"].append(studans)
        else:
           graderstate = {"step": 0, "studans": [studans], "svar": []}
        self.graderstate = graderstate
        return graderstate

