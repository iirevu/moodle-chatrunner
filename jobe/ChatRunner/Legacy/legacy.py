# (C) 2025: Jonas Julius Harang

"""
Code currently not used.
"""

# The following two functions are not used in the present code, but may 
# possibly be used elsewhere. (HGS Aug'25)

def make_data_uri_image(filename):
    with open(filename, 'br') as fin:
        contents = fin.read()
    contents_b64 = base64.b64encode(contents).decode('utf8')
    if filename.endswith('.png'):
        return "data:image/png;base64,{}".format(contents_b64)
    elif filename.endswith('.jpeg') or filename.endswith('.jpg'):
        return "data:image/jpeg;base64,{}".format(contents_b64)
    else:
        return Exception("Unknown file type passed to make_data_uri_image (supported are .png and .jpg/jpeg")

def decorateStudFunction(decorator_name, functionname, codestring):
   decorated_code = re.sub(rf"(^\s*def {functionname}.*:)",rf"@{decorator_name}\1",codestring, flags = re.MULTILINE)
   return decorated_code
