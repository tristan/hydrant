import sys
import dircache

from settings import MEDIA_ROOT

STORAGE_PATH = MEDIA_ROOT + '/workflows/'
STORAGE_FILTERS = ['.xml','.moml']

def listWorkflows():
    list = dircache.listdir(STORAGE_PATH)
    rl = []
    for filter in STORAGE_FILTERS:
        rl.extend([elem for elem in list if filter in elem])
        
    # have to use fqdn due to looping imports      
    rl = [{'id':'.'.join(wf_id.split('.')[:-1]), 'filename':wf_id} for wf_id in rl]
    return rl

def getWorkflowMoML(id):
    """ gets the MoML for a workflow
        id: the storage id of the workflow
            (in this case the file name)
    """
    for ext in STORAGE_FILTERS:
        try:
            f = open(STORAGE_PATH + id + ext, 'r')
            return f.read()
        except:
            pass
    raise IOError('unable to find workflow with id: %s' % id)