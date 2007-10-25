from proxy import *
from kepler.models import *

workflow_cache = {}

def open_workflow_from_object(user, w):
    global workflow_cache
    if w is None or (w.owner != user and w.public == False):
        raise IOError('workflow does not exist')
    if workflow_cache.has_key(w.id):
        return workflow_cache[w.id]
    moml = open(w.get_uri_filename(), 'r').read()
    model = ModelProxy(moml)
    res = (model, w)
    workflow_cache[w.id] = res
    return res

def open_workflow(user, id):
    """
    i am making the assumption that a workflow will always have a unique id,
    unless it is exactly the same workflow.
    """
    global workflow_cache
    try:
        w = Workflow.objects.get(pk=id)
    except:
        w = None
    return open_workflow_from_object(user, w)

def delete_workflow(user, id):
    global workflow_cache
    workflow = Workflow.objects.get(pk=id)
    workflow.delete()
    if workflow_cache.has_key(workflow.id):
        del workflow_cache[workflow.id]
