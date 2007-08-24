from models import *
from utils import KeplerEngine

def open(id):
    print 'opening %s' % id
    try:
        model = openWorkflow(id)
        return {'result': True, 'statistics':model.statistics('')}
    except Exception, e:
        return _processError(e)
    
def structure(id, path=''):
    try:
        structure = getVisualStructure(id, path)
        return {'result': True, 'workflow':structure }
    except Exception, e:
        return _processError(e)

def properties(id, path):
    try:
        props = getActorProperties(id, path)
        return {'result': True, 'actor':{'namespace': '.%s.%s' % (id, path.replace('/','.')), 'name':path.split('/')[-1], 'properties':props }}
    except Exception, e:
        return _processError(e)

def _processError(error):
    if isinstance(error, IOError):
        return {'result':False, 'errors': [{'cause':'IOError','message':error.__str__()}]}
    elif isinstance(error, KeplerEngine.ValidationError):
        return {'result':False, 'errors': error.getValue()}
    else:
        return {'result':False, 'errors': [{'cause':str(error.__class__), 'message':error.__str__()}]}