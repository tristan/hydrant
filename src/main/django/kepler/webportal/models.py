from django.core.cache import cache
from kepler.settings import BACKEND_URL
from django.utils import simplejson

import urllib

def listWorkflows():
    print 'calling listWorkflows'
    return simplejson.loads(urllib.urlopen(BACKEND_URL + 'list/').read())

def proxycall(url):
    return simplejson.loads(urllib.urlopen( '%s%s' % (BACKEND_URL, url.replace(' ', '%20'))).read())

def getProperties(id, path):
    return simplejson.loads(urllib.urlopen( ('%sproperties/%s/%s/' % (BACKEND_URL, id, path)).replace(' ', '%20')).read())

def viewWorkflow(id, path=''):
    print 'calling viewWorkflow'
    data = None
    if path is '':
        data = simplejson.loads(urllib.urlopen('%sstructure/%s/' % (BACKEND_URL, id)).read())
    else:
        data = simplejson.loads(urllib.urlopen('%sstructure/%s/%s/' % (BACKEND_URL, id, path[1:])).read())
    #print data
    return data
