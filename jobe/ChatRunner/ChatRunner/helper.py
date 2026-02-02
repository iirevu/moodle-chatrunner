import os
import toml
import json

def getfn(fn):
    dir = os.path.dirname(os.path.abspath(__file__))
    return( os.path.join( dir, fn ) )


def readobject(fn):
    """
    Read an object from either a toml or json file.
    The filename has to indicate the file format by its extension,
    either .json or .toml.
    """
    if fn[-5:] == ".toml":
        print( "Load file", fn )
        r = toml.load(fn)
    elif fn[-5:] == ".json":
        with open(fn, "rb") as file:
            print( "Opened file", fn )
            r = json.load(file)
    else:
        raise Exception("Need a filename ending in .toml or .json")
    return r
