# Autoreloading launcher.
# Borrowed from Peter Hunt and the CherryPy project (http://www.cherrypy.org).
# Some taken from Ian Bicking's Paste (http://pythonpaste.org/).
#
# Portions copyright (c) 2004, CherryPy Team (team@cherrypy.org)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#     * Neither the name of the CherryPy Team nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os, sys, time, settings
import java.lang.NoClassDefFoundError
try:
    import thread
except ImportError:
    import dummy_thread as thread

# This import does nothing, but it's necessary to avoid some race conditions
# in the threading module. See http://code.djangoproject.com/ticket/2330 .
try:
    import threading
except ImportError:
    pass


RUN_RELOADER = True

def reloader_thread(home):
    mtimes = {}
    win = (sys.platform == "win32")
    #last_mods = []
    while RUN_RELOADER:
#        this_mods = sys.modules.values()
#        for m in [mod for mod in this_mods if mod not in last_mods]:
#            print '===================='
#            print m
#            print getattr(m, "__file__", None)
#        last_mods = this_mods
        try:
            for filename in filter(lambda v: v, map(lambda m: getattr(m, "__file__", None), sys.modules.values())): #[sys.modules[key] for key in sys.modules.keys() if 'vergil' not in key]
                if filename.endswith(".pyc") or filename.endswith("*.pyo"):
                    filename = filename[:-1]
                if not os.path.exists(filename):
                    continue # File might be in an egg, so it can't be reloaded.
                stat = os.stat(filename)
                mtime = stat.st_mtime
                if win:
                    mtime -= stat.st_ctime
                if filename not in mtimes:
                    mtimes[filename] = mtime
                    continue
                if mtime != mtimes[filename]:
                    #print '%s ... %s' % (filename, home)
                    modulename = '.'.join([i for i in filename.split(home)[-1].split('/../')[-1].split('.py')[0].replace('/','.').split('.') if i])
                    print 'reloading module: %s' % modulename
                    #for m in [module for module in sys.modules.keys() if modulename in module]:
                    m = modulename
                    module = sys.modules[m]
                    try:
                        reload(module)
    #                        try:
    #                            getattr(module, '__onreload__')()
    #                        except:
    #                            pass
                        mtimes[filename] = mtime
                    except Exception, e:
                        print 'ERROR!'
                        print e
                    mtimes[filename] = mtime
                    #sys.exit(3) # force reload
        except java.lang.NoClassDefFoundError, e:
            print e.getCause()
        time.sleep(1)

def restart_with_reloader():
    while True:
        args = [sys.executable] + sys.argv
        if sys.platform == "win32":
            args = ['"%s"' % arg for arg in args]
        new_environ = os.environ.copy()
        new_environ["RUN_MAIN"] = 'true'
        exit_code = os.spawnve(os.P_WAIT, sys.executable, args, new_environ)
        if exit_code != 3:
            return exit_code

def main(main_func, home, args=(), kwargs={}):
    #if os.environ.get("RUN_MAIN") == "true":
    
    if True:
        thread.start_new_thread(main_func, args)
        try:
            reloader_thread(home)
        except KeyboardInterrupt:
            pass
    else:
        try:
            sys.exit(restart_with_reloader())
        except KeyboardInterrupt:
            pass