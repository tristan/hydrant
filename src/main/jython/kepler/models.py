import sys, random, os, time, md5
import settings
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
    created = models.DateTimeField('date submitted', auto_now_add=True)
    public = models.BooleanField()
    last_modified_date = models.DateTimeField(auto_now=True)
    """
    def get_errors(self):
        return WorkflowMessage.objects.filter(workflow=self,level='ERROR')
    def get_warnings(self):
        return WorkflowMessage.objects.filter(workflow=self,level='WARNING')
    def get_messages(self):
        return WorkflowMessage.objects.filter(workflow=self,level='MESSAGE')
    """
    def __unicode__(self):
        return unicode(self.name)
    class Admin:
        list_display = ('name', 'owner', 'created', 'last_modified_date', 'public')
"""
class WorkflowMessage(models.Model):
"""    """
    levels:
        * ERROR
        * WARNING
        * MESSAGE
    types:
        * MISSING_ACTOR
        * MISSING_DEPENDENCY
        * UNHANDLED_ENTITY
    """
"""    workflow = models.ForeignKey(Workflow)
    level = models.CharField(max_length=20)
    type = models.CharField(max_length=30)
    message = models.TextField()

"""
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
    creation_date = models.DateTimeField(auto_now_add=True)
    last_modified_date = models.DateTimeField(auto_now=True)
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
        list_display = ('name', 'workflow', 'owner', 'creation_date', 'last_modified_date', 'public')

class TemplateNode(models.Model):
    template = models.ForeignKey(Template)
    property_id = models.CharField(max_length=200)
    description = models.TextField()
    display_name = models.CharField(max_length=50)
    default_value = models.TextField()
    def __unicode__(self):
        return unicode('property "%s" for template "%s"' % (self.display_name, self.template.name))
    class Admin:
        list_display = ('template', 'property_id', 'display_name')

class Job(models.Model):
    template = models.ForeignKey(Template)
    owner = models.ForeignKey(User)
    status = models.CharField(max_length=200)
    submission_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    def get_job_inputs(self):
        return JobInput.objects.filter(job=self)
    def get_job_outputs(self):
        return JobOutput.objects.filter(job=self)
    def __unicode__(self):
        if self.status == 'NEW':
            status = 'New'
        elif self.status == 'QUEUED':
            status = 'Queued'
        elif self.status == 'RUNNING':
            status = 'Running'
        elif self.status == 'DONE':
            status = 'Complete'
        return '%s job created on %s by %s' % (status, self.submission_date, self.owner)
    class Admin:
        list_display = ('submission_date', 'start_date', 'end_date', 'status', 'template', 'owner')

class JobInput(models.Model):
    job = models.ForeignKey(Job)
    node = models.ForeignKey(TemplateNode)
    value = models.TextField()
    class Admin:
        pass

class JobOutput(models.Model):
    job = models.ForeignKey(Job)
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    # types:    TEXT
    #           HTML
    #           XML
    #           IMAGE
    #           FILE
    file = models.CharField(max_length=200)
    creation_date = models.DateTimeField(auto_now_add=True)
    class Admin:
        list_display = ('creation_date', 'job', 'name', 'type', 'file')
