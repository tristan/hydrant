import time, datetime
from threading import Thread, Condition
from java.lang import System
from ptolemy.actor import Manager
from helpers import *

class test_thread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.cond = Condition()
        self.halt = False
    def run(self):
        print 'starting thread: %s' % self
        while not self.halt:
            print 'BOO!'
            self.cond.acquire()
            self.cond.wait(10)
            self.cond.release()
    def boo(self):
        self.cond.acquire()
        self.cond.notifyAll()
        self.cond.release()
    def stop(self):
        self.halt = True
        self.boo()

def start_test():
    threads = []
    for i in range(1):
        t = test_thread()
        t.start()
        threads.append(t)
        time.sleep(0.5)
    keep_running = True
    for i in range(30):
        for t in threads:
            if not t._Thread__stopped:
                keep_running = True
            print '%s: %s' % (t._Thread__name, '...')
            t.boo()
        time.sleep(1)
    for t in threads:
        t.stop()

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
    def queue_job(self, job, model):
        self.queue.append(KeplerExecutionThread(job, model))
        print 'queued new thread: %s' % self.queue[-1]
        self.boo()
default_job_manager = KeplerJobManager()
default_job_manager.start()

class KeplerExecutionThread(Thread):
    def __init__(self, job, model):
        Thread.__init__(self)
        self.model = model
        self.job = job
        mgr = Manager(self.model.model.workspace(), 'manager')
        self.model.model.setManager(mgr)
        self.manager = mgr
        self.job.status = 'QUEUED'
        self.job.save()
    def run(self):
        self.job.status = 'RUNNING'
        self.job.start_date = datetime.datetime.now()
        self.job.save()
        self.manager.execute()
        self.job.status = 'DONE'
        self.job.end_date = datetime.datetime.now()
        self.job.save()
        # TODO: i can see this failing because the thread isn't finished when this command is run
        default_job_manager.boo()
    def get_state(self):
        return self.manager.getState().getDescription()
    def get_iteration_count(self):
        return self.manager.getIterationCount()

def queue_job(job, model):
    t = kepler_execution_thread(job, model)
"""
from kepler.workflow.execution import *
start_test()

from ptolemy.actor import Manager
from kepler.workflow.cache import *
model = open_workflow(None, 22)[0]
m = Manager(model.model.workspace(), 'test')
"""
