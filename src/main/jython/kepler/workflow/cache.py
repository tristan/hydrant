from proxy import *
from kepler.models import *
from django.shortcuts import get_object_or_404

workflow_cache = {}

def open_workflow_from_object(user, w):
    global workflow_cache
    if workflow_cache.has_key(w.id):
        return workflow_cache[w.id]
    model = w.get_proxy_object()
    res = (model, w)
    workflow_cache[w.id] = res
    return res

def open_workflow(user, id):
    """
    i am making the assumption that a workflow will always have a unique id,
    unless it is exactly the same workflow.
    """
    global workflow_cache
    w = get_object_or_404(Workflow,pk=id)
    return open_workflow_from_object(user, w)
