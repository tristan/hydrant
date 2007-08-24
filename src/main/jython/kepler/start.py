import os, sys, dircache, getopt

def setup_environ(settings_mod):
    """
    Configure the runtime environment. This can also be used by external
    scripts wanting to set up a similar environment to manage.py.
    """
    # Add this project to sys.path so that it's importable in the conventional
    # way. For example, if this file (manage.py) lives in a directory
    # "myproject", this code would add "/path/to/myproject" to sys.path.
    print sys.path
    project_directory, settings_filename = os.path.split(settings_mod.__file__)
    project_name = os.path.basename(project_directory)
    settings_name = os.path.splitext(settings_filename)[0]
    #sys.path.append(os.path.join(project_directory))
    sys.path.append('/'.join(os.path.join(project_directory).split('/')[:-1]))
    project_module = __import__(project_name, {}, {}, [''])
    print sys.path
    sys.path.pop()
    print sys.path

    # Set KEPLER_BACKEND_SETTINGS_MODULE appropriately.
#    os.environ['KEPLER_BACKEND_SETTINGS_MODULE'] = '%s.%s' % (project_name, settings_name)
    return project_directory

def loadlibs():
    jars = dircache.listdir(settings.LIB_DIRECTORY)
    #print jars
    for jar in jars:
        #print '/'.join([settings.LIB_DIRECTORY + jar])
        sys.path.append('/'.join([settings.LIB_DIRECTORY, jar]))
    print sys.path

if __name__ == "__main__":
    try:
        import settings # Assumed to be in the same directory.
    except ImportError:
        import sys
        sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
        sys.exit(1)
    project_directory = setup_environ(settings)
    
    loadlibs()
    
    args = sys.argv[1:]
    if args[0] == 'server':
        
        import autoreload
        from server import runserver
        
        autoreload.main(runserver, project_directory)
        
    elif args[0] == 'shell':
        
        from utils import WorkflowCache, KeplerEngine
        from models import getActors
        from ptolemy.actor import Manager, CompositeActor, Actor, Director
        from ptolemy.kernel import Relation, Port
        from ptolemy.vergil.kernel.attributes import TextAttribute
        
        getModelResult = WorkflowCache().getModel('1plus1')
        if getModelResult['result']:
            m = getModelResult['model']
        
        l = lambda s: [i for i in s.containedObjectsIterator()]
        
        r = [i for i in m.containedObjectsIterator() if isinstance(i, Relation)]
        a = [i for i in m.containedObjectsIterator() if isinstance(i, Actor)]
        p = [i for i in m.containedObjectsIterator() if isinstance(i, Port)]
        t = [i for i in m.containedObjectsIterator() if isinstance(i, TextAttribute)]