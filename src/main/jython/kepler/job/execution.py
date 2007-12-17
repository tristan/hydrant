import time, datetime, sys
from threading import Thread, Condition
from java.lang import System
import java.lang.Exception
from ptolemy.actor import Manager
from ptolemy.kernel.util import IllegalActionException, KernelException
from helpers import *

class KeplerJobManager(Thread):
    def __init__(self, max_active=2):
        Thread.__init__(self)
        self.max_active = max_active
        self.queue = []
        self.running = []
        #self.complete = []
        self.cond = Condition()
        self.halt = False
    def run(self):
        while not self.halt:
            if len(self.queue) > 0 and len(self.running) < self.max_active:
                t = self.queue.pop()
                print 'starting thread: %s' % t
                self.running.append(t)
                t.start()
            elif len(self.running) > 0:
                # check all the running threads to see if they've completed
                for t in self.running:
                    if t._Thread__stopped:
                        #self.complete.append(t)
                        self.running.remove(t)
                        print 'removed thread: %s' % t
            else:
                self.cond.acquire()
                self.cond.wait(60)
                self.cond.release()
    def boo(self):
        self.cond.acquire()
        self.cond.notifyAll()
        self.cond.release()
    def shutdown(self):
        self.halt = True
        self.boo()
    def queue_job(self, job, model, replacement_manager):
        self.queue.append(KeplerExecutionThread(job, model, replacement_manager))
        print 'queued new thread: %s' % self.queue[-1]
        self.boo()
default_job_manager = KeplerJobManager()
default_job_manager.start()

class KeplerExecutionThread(Thread):
    def __init__(self, job, model, replacement_manager):
        Thread.__init__(self)
        self.model = model
        self.job = job
        self.replacement_manager = replacement_manager
        mgr = Manager(self.model.model.workspace(), 'manager')
        self.model.model.setManager(mgr)
        self.manager = mgr
        self.job.status = 'QUEUED'
        self.job.save()
    def run(self):
        try:
            self.job.status = 'RUNNING'
            self.job.start_date = datetime.datetime.now()
            self.job.save()
            self.manager.execute()
            self.job.status = 'DONE'
            error = None
        except java.lang.Exception, e:
            error = {'name': 'Exception', 'type':'TEXT', 'output': KernelException.stackTraceToString(e) }
            self.job.status = 'ERROR'
        if error is not None:
            self.replacement_manager.writePythonData(error)
        self.job.end_date = datetime.datetime.now()
        self.job.save()
        default_job_manager.boo()
    def get_state(self):
        return self.manager.getState().getDescription()
    def get_iteration_count(self):
        return self.manager.getIterationCount()

#def queue_job(job, model):
#    t = kepler_execution_thread(job, model)
"""
from kepler.workflow.execution import *
start_test()

from ptolemy.actor import Manager
from kepler.workflow.cache import *
model = open_workflow(None, 22)[0]
m = Manager(model.model.workspace(), 'test')
"""
