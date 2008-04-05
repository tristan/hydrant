from proxy import *
from hydrant.models import *
from django.shortcuts import get_object_or_404

workflow_cache = {}

def open_workflow_from_object(user, w):
    """ Checks the workflow cache for an already cached copy of the
    requested workflow's proxy object, and returns a tuple containing
    the Proxy object and the Workflow object. If the workflow isn't in
    the cache, it creates a workflow proxy object and stores it in the
    cache before returning it.
    """
    global workflow_cache
    if workflow_cache.has_key(w.id):
        return workflow_cache[w.id]
    model = w.get_proxy_object()
    res = (model, w)
    workflow_cache[w.id] = res
    return res

def open_workflow(user, id):
    """ Retrieves a Workflow object from the database id, passes it to
    open_workflow_from_object and returns the result.
    """
    global workflow_cache
    w = get_object_or_404(Workflow,pk=id)
    return open_workflow_from_object(user, w)
