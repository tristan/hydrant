import os, traceback
from django.utils import simplejson

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

def readMetadataFile(directory, filename):
    m = open('%s/.%s.metadata' % (directory, filename), 'r')
    try:
        return simplejson.loads(m.read())
    except:
        traceback.print_exc()
        raise('metadata file for %s/%s is invalid!' % (directory, filename))

def readFile(directory, filename):
    """
    reads a file from storage 
    returns a tuple containing the file contents, and the metadata dict
    """
    f = open('%s/%s' % (directory, filename), 'r')
    return (f.read(), readMetadataFile(directory, filename))
