import sys, random, os, time, md5
import storage, settings
from StringIO import StringIO

#import utils
#from utils import KeplerEngine, WorkflowCache

from java.lang import System
from java.io import ByteArrayOutputStream, PrintStream

import ptolemy
from ptolemy.actor import Manager, CompositeActor, Actor, Director
from ptolemy.moml import MoMLParser, Vertex
from ptolemy.moml.filter import RemoveGraphicalClasses
from ptolemy.kernel import Relation, Port
from ptolemy.vergil.kernel.attributes import TextAttribute
from ptolemy.vergil.basic import KeplerDocumentationAttribute
from ptolemy.actor.gui import SizeAttribute
from org.kepler.sms import SemanticType
from org.kepler.moml import NamedObjId

"""
def executeWorkflow(id):

    moml = storage.getWorkflowMoML(id)

    parser = MoMLParser()
    toplevel = parser.parse(moml)
    manager = Manager(toplevel.workspace(), "jythonManager")
    toplevel.setManager(manager)

    bso = ByteArrayOutputStream()
    bse = ByteArrayOutputStream()
    defaultout = System.out
    defaulterr = System.err
    System.setOut(PrintStream(bso))
    System.setErr(PrintStream(bse))
    try:
        print 'executing workflow...'
        manager.execute()
        success = True
        print '...execution successful'
    except Exception, e:
        print '...execution failed'
        success = False

    standardout = bso.toString()
    standarderr = bse.toString()
    System.setOut(defaultout)
    System.setErr(defaulterr)
    return {'stdout': standardout, 'stderr': standarderr, 'success': success }
"""


from django.db import models
from django.contrib.auth.models import User

class Workflow(models.Model):
    """
    a database representation of a model.
    just stores metadata and URI to the workflow
    """
    uri = models.FileField(upload_to='workflows')
    name = models.CharField(max_length=50)
    owner = models.ForeignKey(User)
    created = models.DateTimeField('date submitted')
    public = models.BooleanField()
    def __unicode__(self):
        return unicode(self.name)
    class Admin:
        pass


class WorkflowChange(models.Model):
    workflow = models.ForeignKey(Workflow)
    prev = models.IntegerField()
    change_desc = models.TextField()

class Template(models.Model):
    workflow = models.ForeignKey(Workflow)
    owner = models.ForeignKey(User)
    public = models.BooleanField()
    name = models.CharField(max_length=50)
    description = models.TextField()
    def get_all_nodes(self):
        return TemplateNode.objects.filter(template=self)
    def get_node_with_id(self, property_id):
        f = TemplateNode.objects.filter(template=self,property_id=property_id)
        if f:
            return f[0]
        else:
            return None
    def __unicode__(self):
        return unicode('%s, a template for workflow: %s' % (self.name, self.workflow))
    class Admin:
        pass

class TemplateNode(models.Model):
    template = models.ForeignKey(Template)
    property_id = models.CharField(max_length=200)
    description = models.TextField()
    display_name = models.CharField(max_length=50)
    default_value = models.TextField()
    def __unicode__(self):
        return unicode('property "%s" for template "%s"' % (self.display_name, self.template.name))
    class Admin:
        pass
