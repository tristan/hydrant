import os, array

from ptolemy.actor import Initializable, TypedAtomicActor, TypedIOPort
from ptolemy.data.type import BaseType
from ptolemy.data import StringToken
from ptolemy.kernel.util import SingletonAttribute
from ptolemy.data.expr import StringParameter
from ptolemy.moml import MoMLFilter, MoMLParser
from au.edu.jcu.kepler.kts import ReplacementManager

from settings import STORAGE_ROOT
from kepler.models import *

class TestRM(ReplacementManager):
    """
    a testing replacement manager
    just prints the received data to the console
    """
    def __init__(self, container, name):
        ReplacementManager.__init__(self, container, name)
        self.storage_directory = StringParameter(self, "storage directory")

    def writePythonData(self, data):
        print type(data)
        print data
        job_name = data.get('name', 'unnamed')
        job_type = data.get('type', 'unknown')

class DefaultReplacementManager(ReplacementManager):
    def __init__(self, container, name, jobid):
        ReplacementManager.__init__(self, container, name)
        self.jobid = jobid
        os.makedirs('%s/%s/' % (STORAGE_ROOT, self.jobid))
    def writePythonData(self, data):
        output = data.get('output', None)
        if output != None:
            name = data.get('name', 'unnamed')
            type = data.get('type', 'unknown')
            binary = (type == 'BINARY' or type == 'IMAGE')
            ext = type
            if type == 'IMAGE':
                ext = data.get('format', 'RAW')
            file_name = '%s/%s/%s.%s' % (STORAGE_ROOT, self.jobid, name.replace('.', '_'), ext)
            f = open(file_name, 'w%s' % (binary and 'b' or '',))
            if isinstance(output, array.array):
                output.tofile(f)
            else:
                f.write(output)
            f.close()
            j = JobOutput(name=name, type=type, file=file_name, job=Job.objects.get(pk=self.jobid))
            j.save()

"""
from kepler.workflow.components import *
from kepler.workflow.cache import *
from kepler.workflow.proxy import *
from ptolemy.actor.lib.gui import Display
from au.edu.jcu.kepler.kts import WebServiceFilter
oldmp = open_workflow(None, 24)[0]
moml = oldmp.get_xml()
mp = ModelProxy(moml, [WebServiceFilter()])
mp.model.workspace().getWriteAccess()
RM(mp.model, 'replacement-manager')
mp.model.workspace().doneWriting()
mgr = Manager(mp.model.workspace(), 'manager')
mp.model.setManager(mgr)
mgr.execute()
"""
