from helpers import *
from execution import default_job_manager
from kepler.workflow.proxy import ModelProxy

from au.edu.jcu.kepler.hydrant import WebServiceFilter


def open_workflow_for_execution(user, w):
    moml = open(w.get_moml_file_filename(), 'r').read()
    return ModelProxy(moml, [WebServiceFilter()])

def queue_new_job(job):
    model = open_workflow_for_execution(job.owner, job.workflow)
    model.model.workspace().getWriteAccess()
    for input in job.get_job_inputs():
        id = input.parameter.property_id
        il = id.split('.')[1:]
        path_to_actor = il[1:-1]
        prop = il[-1]
        print '(%s, %s, %s)' % (path_to_actor, prop, input.value)
        model.set_actor_property(path_to_actor, prop, input.value)
    drm = DefaultReplacementManager(model.model, 'replacement-manager', job.pk)
    prov = ProvenanceListenerWrapper(model.model, 'provenancelistener', job.pk)
    modify_rexpression_actors(model.model, drm)
    model.model.workspace().doneWriting()
    default_job_manager.queue_job(job, model, drm)
