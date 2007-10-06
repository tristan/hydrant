from models import *
from workspaces import *
from workflow.utils import ValidationError
from django.http import Http404, HttpResponse
from django.utils import simplejson
from django.contrib.auth.decorators import login_required

import repository
import workflow
import debug
import traceback

def list(request):
    debug.print_request_info(request)
    pub, pri = repository.list(request.user.username)
    l = []
    for i in pub:
        l.append({'id':i[0], 'public': True, 'metadata':i[1]})
    for i in pri:
        l.append({'id':i[0], 'public': False, 'metadata':i[1]})
    return _JSONResponse({'workflows': l})
list = login_required(list)

def set_property(request):
    if not request.POST.has_key('__namespace__'):
        raise Http404('__namespace__ missing from form')
    namespace = request.POST.get('__namespace__')
    try:
        ws = request.session['workspace']
        if ws is None:
            raise('')
    except:
        raise Http404('no workspace exists for user: %s' % request.user.username)
    try:
        ws = get_model_from_workspace(request.user.username, ws)
    except:
        request.session['workspace'] = ''
        request.session.modified = True
        raise Http404('error accessing workspace, removing this workspace from the session')
    try:
        actor_path = namespace.split('.')[2:]
    except:
        raise Http404('invalid namespace: %s' % namespace)

    for i in request.POST:
        if i != '__namespace__' and i != 'class':
            print 'OLD VALUE: %s: %s' % (i, ws.get_actor_property(actor_path, i))
            ws.set_actor_property(actor_path, i, request.POST[i])

    return _JSONResponse({'result':True})
set_property = login_required(set_property)

def new_workspace(request, id):
    username = request.user.username
    print 'creating new workflow for user: %s' % username
    try:
        request.session['workspace'] = create_workspace(username, id)
        request.session.modified = True
        return _JSONResponse({'result': True})
    except Exception, e:
        traceback.print_exc()
        return _processError(e)
new_workspace = login_required(new_workspace)

def structure(request, id, path=''):
    try:
        #structure = getVisualStructure(id, path)
        model, meta = workflow.cache.open_workflow(request.user.username, id)
        res = model.get_as_dict([i for i in path.split('/') if i != ''])
        res['id'] = id
        res['metadata'] = meta
        return _JSONResponse({'result': True, 'workflow':res })
    except Exception, e:
        import traceback
        traceback.print_exc()
        return _processError(e)

def properties(request, id, path):
    try:
        #props = getActorProperties(id, path)
        model, meta = workflow.cache.open_workflow(request.user.username, id)
        path = path.split('/')
        print path
        props = model.get_properties(path)
        return _JSONResponse({'result': True, 'actor':{'namespace': '.%s.%s' % (id, '.'.join(path)), 'name':path[-1], 'properties':props }})
    except Exception, e:
        return _processError(e)

def _JSONResponse(json):
    json = simplejson.dumps(json)
    return HttpResponse('%s' % json, mimetype='text/plain')

def _processError(error):
    #if isinstance(error, IOError):
    #    ret = {'result':False, 'errors': [{'cause':'IOError','message':error.__str__()}]}
    if isinstance(error, ValidationError):
        ret = {'result':False, 'errors': error.getValue()}
        return _JSONResponse(ret)
    #else:
    #    ret = {'result':False, 'errors': [{'cause':str(error.__class__), 'message':error.__str__()}]}
    #return _JSONResponse(ret)
    #raise Http404(error)
    raise error
