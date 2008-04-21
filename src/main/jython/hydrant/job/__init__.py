from helpers import *
from execution import default_job_manager

def queue_new_job(job):
    model = job.workflow.get_proxy_object(True)
    pe = model.proxied_entity
    pe.workspace().getWriteAccess()
    for input in job.get_job_inputs():
        id = input.parameter.property_id
        il = id.split('.')[1:]
        path_to_actor = il[1:-1]
        prop = il[-1]
        print '(%s, %s, %s)' % (path_to_actor, prop, input.value)
        model.set_actor_property(path_to_actor, prop, input.value)
    drm = DefaultReplacementManager(pe, 'replacement-manager', job.pk)
    prov = ProvenanceListenerWrapper(pe, 'provenancelistener', job.pk)
    modify_rexpression_actors(pe, drm)
    pe.workspace().doneWriting()
    default_job_manager.queue_job(job, model, drm)

def stop_job(job):
    default_job_manager.stop_job(job)
