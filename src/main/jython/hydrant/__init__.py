from jython import settings as settings_mod
import os
import sys

if hasattr(settings_mod, 'LIB_DIRECTORY'):
    from java.net import URL, URLClassLoader
    from java.io import File
    from java.lang import ClassLoader
    # add jars to the java classpath which seems to be different from the jython one somehow
    # from: http://forum.java.sun.com/thread.jspa?threadID=300557
    def _add_to_java_classpath(s):
        sysloader = ClassLoader.getSystemClassLoader()
        sysclass = URLClassLoader([URL("file:///")]).class
        try:
            method = sysclass.getDeclaredMethod("addURL",[URL("file:///").getClass()])
            method.setAccessible(True)
            method.invoke(sysloader, [File(s).toURL()])
        except:
            pass

    def _add_jar(j):
        sys.path.append(j)
        _add_to_java_classpath(j)

    def _do_add_libs(s):
        if os.path.isfile(s):
            for i in open(s).read().split(':'):
                _add_jar(i)
        else:
            for i in os.listdir(s):
                jar = '/'.join([s, i])
                if os.path.isfile(jar):
                    if i.lower().endswith('.jar'):
                        _add_jar(jar)
                else:
                    _do_add_libs(jar)
            
    if isinstance(settings_mod.LIB_DIRECTORY, (tuple, list, dict)):
        for i in settings_mod.LIB_DIRECTORY:
            try:
                _do_add_libs(i)
            except OSError:
                pass
    else:
        _do_add_libs(settings_mod.LIB_DIRECTORY)
