from django.db import models
from django.contrib.auth.models import User
import widgets
from workflow.proxy import ModelProxy

class Workflow(models.Model):
    """
    a database representation of a model.
    just stores metadata and URI to the workflow
    """
    moml_file = models.FileField(upload_to='workflows', verbose_name=_('Workflow file'))
    name = models.CharField(max_length=50)
    owner = models.ForeignKey(User, related_name="worklow_owner",)
    created = models.DateTimeField('date submitted', auto_now_add=True)
    public = models.BooleanField(default=False)
    description = models.TextField()
    deleted = models.BooleanField(default=False,)
    valid_users = models.ManyToManyField(User, verbose_name=_('valid users'), blank=True, filter_interface=models.HORIZONTAL, related_name="workflow_valid_users")
    def get_parameter(self, id):
        return WorkflowParameter.objects.get(workflow=self, property_id=id);
    def get_all_parameters(self):
        return WorkflowParameter.objects.filter(workflow=self);
    def get_exposed_parameters(self):
        return WorkflowParameter.objects.filter(workflow=self, expose_to_user=True);
    def __unicode__(self):
        return unicode(self.name)
    def get_model(self):
        moml = open(self.get_moml_file_filename(), 'r').read()
        return ModelProxy(moml)
    class Admin:
        list_display = ('name', 'owner', 'created', 'public')
        search_fields = ('name', 'description')
        date_hierarchy = 'created'
    class Search:
        list_display = ('name', 'description')
        search_fields = ('name', 'description')
        sortable = ('name',)

class WorkflowParameter(models.Model):
    workflow = models.ForeignKey(Workflow)
    property_id = models.CharField(max_length=200, editable=False)
    expose_to_user = models.BooleanField()
    description = models.TextField()
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=1000)
    type = models.CharField(max_length=50)
    def __unicode__(self):
        return unicode('parameter "%s" for workflow "%s"' % (self.name, self.workflow.name))
    class Admin:
        list_display = ('workflow', 'property_id', 'name')

class Job(models.Model):
    workflow = models.ForeignKey(Workflow)
    owner = models.ForeignKey(User)
    status = models.CharField(max_length=200)
    submission_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    name = models.CharField(max_length=200, null=True)
    description = models.TextField(null=True)
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
        elif self.status == 'ERROR':
            status = 'Error'
        else:
            status = 'Unknown'
        #return '%s job created on %s by %s' % (status, self.submission_date, self.owner)
        if self.name is None or self.name == '':
            return '%s Job' % self.workflow
        else:
            return self.name
    class Admin:
        list_display = ('workflow', 'submission_date', 'start_date', 'end_date', 'status', 'owner')
        search_fields = ('workflow__name', 'status',)
        list_filter = ('status',)
        date_hierarchy = 'submission_date'
    class Search:
        list_display = ('name', 'workflow', 'status', 'submission_date', 'end_date')
        search_fields = ('workflow__name', 'status', 'name', 'description')
        sortable = ('workflow__name',)

class JobInput(models.Model):
    job = models.ForeignKey(Job)
    parameter = models.ForeignKey(WorkflowParameter)
    type = models.CharField(max_length=50)
    # types:    SELECT
    #           INPUT
    #           TEXT
    #           CHECKBOX
    #           FILE
    value = models.TextField()
    class Admin:
        pass

class JobOutput(models.Model):
    job = models.ForeignKey(Job)
    name = models.CharField(max_length=200)
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

