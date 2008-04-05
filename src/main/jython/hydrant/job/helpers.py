import os
import array
import random

from ptolemy.actor import Initializable, TypedAtomicActor, TypedIOPort
from ptolemy.data.type import BaseType
from ptolemy.data import StringToken
from ptolemy.kernel.util import SingletonAttribute, Attribute
from ptolemy.data.expr import StringParameter
from ptolemy.moml import MoMLFilter, MoMLParser
from au.edu.jcu.kepler.hydrant import ReplacementManager
from org.kepler.provenance import ProvenanceListener, TextFileRecording

from org.ecoinformatics.seek.R import RExpression
from ptolemy.actor.lib.io import LineWriter
from org.geon import BinaryFileWriter

from settings import STORAGE_ROOT
from hydrant.models import *

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
        try:
            os.makedirs('%s/jobs/%s/' % (STORAGE_ROOT, self.jobid))
        except:
            if not os.path.exists('%s/jobs/%s/' % (STORAGE_ROOT, self.jobid)):
                raise
    def writePythonData(self, data):
        output = data.get('output', None)
        if output == None:
            output = ''
        name = data.get('name', 'unnamed')
        type = data.get('type', 'unknown')
        file_name = data.get('filename', None)
        if file_name == None:
            binary = (type == 'BINARY' or type == 'IMAGE')
            ext = type
            if type == 'IMAGE':
                ext = data.get('format', 'RAW')
            file_name = '%s/jobs/%s/%s.%s' % (STORAGE_ROOT, self.jobid, name.replace('.', '_'), ext)
            f = open(file_name, 'w%s' % (binary and 'b' or '',))
            if isinstance(output, array.array):
                output.tofile(f)
            else:
                f.write(output)
            f.close()
        j = JobOutput(name=name, type=type, file=file_name, job=Job.objects.get(pk=self.jobid))
        j.save()
    def get_storage_dir(self):
        return '%s/jobs/%s' % (STORAGE_ROOT, self.jobid)

class ProvenanceListenerWrapper(ProvenanceListener):
    def __init__(self, container, name, jobid):
        Attribute.__init__(self, container, name)
        file_name = '%s/jobs/%s/provenance.txt' % (STORAGE_ROOT, jobid)
        self.recordingType.setExpression('Text File')
        self.attributeChanged(self.recordingType)
        try:
            f = [p for p in self.attributeList() if p.getName() == "Filename"][0]
        except:
            raise Exception('unable to find Filename property in provenance listener actor')
        f.setExpression(file_name)
        jo = JobOutput(name='Provenance Data', type='TEXT', file=file_name, job=Job.objects.get(pk=jobid))
        jo.save()

def modify_rexpression_actors(model, replacement_manager):
    for e in model.allAtomicEntityList():
        if isinstance(e, RExpression):
            e.Rcwd.setExpression(replacement_manager.get_storage_dir())
        elif isinstance(e, (LineWriter, BinaryFileWriter)):
            e.fileName.setExpression('%s/%s' % (replacement_manager.get_storage_dir(), e.getName()))
    for e in model.allCompositeEntityList():
        modify_rexpression_actors(e, replacement_manager)

