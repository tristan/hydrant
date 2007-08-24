from kepler.settings import MEDIA_ROOT
import dircache

STORAGE_PATH = MEDIA_ROOT + '/workflows/'
STORAGE_FILTERS = ['.xml','.moml']
    
def readWorkflow(id):
    """ gets a workflow from storage 
        id: the storage id of the workflow
            (in this case the file name)
    """
    
    f = open(STORAGE_PATH + id, 'r')
    return f.read()

def listWorkflows():
    list = dircache.listdir(STORAGE_PATH)
    rl = []
    for filter in STORAGE_FILTERS:
        rl.extend([elem for elem in list if filter in elem])
        
    # have to use fqdn due to looping imports      
    rl = [{'name':kepler.backend.models.getWorkflow(wf_id)['name'], 'id':wf_id} for wf_id in rl]
    return rl