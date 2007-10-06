#!/usr/bin/env jython
from django.core.management import execute_manager
try:
    import settings # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

def testing():
    from ptolemy.data.expr import Constants
    return giveMeError(Constants.types)

def giveMeError(function):
    import java.lang.ExceptionInInitializerError
    try:
        function.__call__()
    except java.lang.ExceptionInInitializerError, e:
        return e

if __name__ == "__main__":
    import sys
    sys.path.append('/home/tristan/projects/jcu/WebPortal/src/test/java')
    sys.path.append('/home/tristan/projects/jcu/WebPortal/src/test/jython')
    from java.lang import System
    System.setProperty('ptolemy.ptII.dir', '')
    execute_manager(settings)
