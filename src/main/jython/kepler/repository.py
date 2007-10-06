import sys, dircache, md5, time, urllib, os

from settings import MEDIA_ROOT
from django.utils import simplejson
from storage import *
import traceback
from kepler.models import Workflow

STORE_PATH = MEDIA_ROOT + '/workflows'
PUBLIC_STORAGE = '__public__'

def list(username):
    public_list = []
    private_list = []
    try:
        public_list = [(i, readMetadataFile('%s/%s' % (STORE_PATH, PUBLIC_STORAGE), i)) for i in dircache.listdir('%s/%s' % (STORE_PATH, PUBLIC_STORAGE)) if not i.startswith('.')]
    except:
        traceback.print_exc() # cause there are no workflows yet!
    try:
        private_list = [(i, readMetadataFile('%s/%s' % (STORE_PATH, username or '__none__'), i)) for i in dircache.listdir('%s/%s' % (STORE_PATH, username or '__none__')) if not i.startswith('.')]
    except:
        traceback.print_exc() # cause the folder probably doesn't exist yet, or username is None
    return (public_list, private_list,)

def storeWorkflow(username, name, moml, public=False):
    """
    stores a file in the repository
    returns the id for the newly created file

    TODO: if file exists?
    """
    filename = md5.new('%s%s%s' % (username, name, moml)).hexdigest()

    metadata = { 'name': name,
                 'owner': username,
                 'created': time.strftime('%Y-%m-%d %H:%M:%S %Z', time.localtime(time.time()))
            }
    #writeFile('%s/%s' % (STORE_PATH, public and PUBLIC_STORAGE or username), filename, moml, metadata)
    return filename

def retreiveWorkflow(username, id):
    if not username:
        username = PUBLIC_STORAGE
    try:
        # try read from users store
        return readFile('%s/%s' % (STORE_PATH, username), id)
    except:
        # try read from public store
        return readFile('%s/%s' % (STORE_PATH, PUBLIC_STORAGE), id)


def writeFile(directory, filename, filecontents, metadata):
    if not os.path.exists(directory):
        os.makedirs(directory)
    f = open('%s/%s' % (directory, filename), 'w')
    f.write(filecontents)
    f.close()
    f = open('%s/.%s.metadata' % (directory, filename), 'w')
    f.write(simplejson.dumps(metadata))
    f.close()
    return 'file://%s/%s' % (directory, filename)

def readFile(directory, filename):
    """
    reads a file from storage 
    returns a tuple containing the file contents, and the metadata dict
    """

    f = open('%s/%s' % (directory, filename), 'r')
    return (f.read(), readMetadataFile(directory, filename))
