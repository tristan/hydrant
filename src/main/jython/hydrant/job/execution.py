import time, datetime, sys
from threading import Thread, Condition
from java.lang import System
import java.lang.Exception
from ptolemy.actor import Manager
from ptolemy.kernel.util import IllegalActionException, KernelException
from helpers import *
from hydrant.models import Message, JobMessage, get_system_user
from hydrant.templatetags.textutils import timeuntil_with_secs
from settings import MAX_RUNNING_JOBS

class KeplerJobManager(Thread):
    def __init__(self, max_active=MAX_RUNNING_JOBS):
        Thread.__init__(self)
        self.max_active = max_active
        self.queue = []
        self.running = {}
        #self.complete = []
        self.cond = Condition()
        self.halt = False
    def run(self):
        while not self.halt:
            if len(self.queue) > 0 and len(self.running) < self.max_active:
                t = self.queue.pop()
                print 'starting thread: %s' % t
                self.running[t.job] = t
                t.start()
            elif len(self.running) > 0:
                # check all the running threads to see if they've completed
                for job in self.running:
                    if not self.running[job].isAlive():
                        #self.complete.append(t)
                        t = self.running.pop(job)
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
    def stop_job(self, job):
        t = self.running.get(job, None)
        if t == None:
            for t in self.queue:
                if t.job == job:
                    self.queue.remove(t)
                    return
            # if we get to here then the job has stopped before getting here
            # or something has gone wrong somewhere else
        else:
            t.stop()

                
            
default_job_manager = KeplerJobManager()
default_job_manager.start()

class KeplerExecutionThread(Thread):
    def __init__(self, job, model, replacement_manager):
        Thread.__init__(self)
        self.model = model
        self.job = job
        self.replacement_manager = replacement_manager
        mgr = Manager(self.model.proxied_entity.workspace(), 'manager')
        self.model.proxied_entity.setManager(mgr)
        self.manager = mgr
        self.job.status = 'QUEUED'
        self.job.save()
    def run(self):
        try:
            self.job.status = 'RUNNING'
            self.job.start_date = datetime.datetime.now()
            self.job.save()

            msg = Message(touser=self.job.owner,
                          fromuser=get_system_user(),
                          verb='started',
                          text='Estimated time till completion: %s' % timeuntil_with_secs(self.job.get_eta())
                          )
            msg.save()
            JobMessage(job=self.job, message=msg).save()

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

        msg = Message(touser=self.job.owner,
                      fromuser=get_system_user(),
                      verb='ended',
                      text='')
        if self.job.status == 'DONE':
            msg.text = 'Job completed successfully'
        else:
            msg.text = 'Job ended with errors'
        msg.save()
        JobMessage(job=self.job, message=msg).save()
        
        default_job_manager.boo()
    def stop(self):
        self.job.status = 'STOPPING'
        self.job.save()
        self.manager.stop()
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
