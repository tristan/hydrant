from helpers import *
from hydrant.models import JobInput
from execution import default_job_manager

def queue_new_job(job):
    """ This function loads an instance of workflow and prepares
    it for execution.
    """
    # get the workflow instance
    model = job.workflow.get_proxy_object(True)
    # the proxied entity is the base level object for the workflow.
    pe = model.proxied_entity
    pe.workspace().getWriteAccess()
    params_set = []
    # this section goes through the list of job inputs for this job
    # and sets each of the related workflow parameters to the values
    # specified by the job inputs.
    for input in job.get_job_inputs():
        id = input.parameter.property_id
        params_set.append(input.parameter)
        il = id.split('.')[1:]
        path_to_actor = il[1:-1]
        prop = il[-1]
        print '(%s, %s, %s)' % (path_to_actor, prop, input.value)
        model.set_actor_property(path_to_actor, prop, input.value)
    # the following section goes through a list of workflow parameters
    # set by the owner of the workflow.
    for param in job.workflow.get_all_parameters():
        # this filters out any parameters that are set as job inputs
        # so that they don't get overwritten by the default values.
        if param not in params_set:
            id = param.property_id
            il = id.split('.')[1:]
            path_to_actor = il[1:-1]
            prop = il[-1]
            model.set_actor_property(path_to_actor, prop, param.value)
            JobInput(job=job, parameter=param,value=param.value).save()
    # Add a replacement manager to the workflow instance.
    drm = DefaultReplacementManager(pe, 'replacement-manager', job.pk)
    #prov = ProvenanceListenerWrapper(pe, 'provenancelistener', job.pk)
    # check for r-expression actors and modify them for Hydrant.
    modify_rexpression_actors(pe, drm)
    pe.workspace().doneWriting()
    # queue the job
    default_job_manager.queue_job(job, model, drm)

def stop_job(job):
    default_job_manager.stop_job(job)
