import urllib

def percent_encode(string):
    return urllib.quote(string.encode('utf-8'), '~')

