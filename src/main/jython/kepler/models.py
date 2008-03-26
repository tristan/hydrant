from django.db import models
from django.contrib.auth.models import User
import widgets
from workflow.proxy import EntityProxy


class Workflow(models.Model):

    """ Stores the MoML file for a workflow along with associated
    metadata.

    moml_file -- The MoML file,
    name -- The verbose name of the Workflow,
    owner -- The User whom uploaded the Workflow.
    created -- The Date/Time which the Workflow was uploaded.
    public -- Whether the Workflow is publically accessable or not.
    description -- A long description of the Workflow.
    deleted -- True if the workflow should be considered deleted.
    valid_users -- Users who're able to access this Workflow in the case
    that it is not public.
    """

    moml_file = models.FileField(upload_to='workflows', 
                                 verbose_name='Workflow file')
    name = models.CharField(max_length=50)
    owner = models.ForeignKey(User, related_name="worklow_owner",)
    created = models.DateTimeField('date submitted', auto_now_add=True)
    public = models.BooleanField(default=False)
    description = models.TextField()
    deleted = models.BooleanField(default=False,)
    valid_users = models.ManyToManyField(User, verbose_name='valid users', 
                                         blank=True, 
                                         filter_interface=models.HORIZONTAL, 
                                         related_name='workflow_valid_users')

    def get_parameter(self, id):
        """ Gets a WorkflowParameter object linked to this Workflow.
        """
        return WorkflowParameter.objects.get(workflow=self, property_id=id);

    def get_all_parameters(self):
        """ Returns a list of all WorkflowParameter objects linked to
        this Workflow.
        """
        return WorkflowParameter.objects.filter(workflow=self);

    def get_exposed_parameters(self):
        """ Returns a list of all the WorkflowParameter objects linked
        to this workflow which have expose_to_user equal to True.
        """
        return WorkflowParameter.objects.filter(workflow=self, 
                                                expose_to_user=True);

    def __unicode__(self):
        return unicode(self.name)

    def get_proxy_object(self):
        """ Returns a kepler.workflow.proxy.EntityProxy object which
        proxies this Workflow.
        """
        moml = open(self.get_moml_file_filename(), 'r').read()
        return EntityProxy(moml)

    class Admin:
        list_display = ('name', 'owner', 'created', 'public')
        search_fields = ('name', 'description')
        date_hierarchy = 'created'

    class Search:

        """ Class used by the kepler.portalviewshelper.SearchList class.
        """

        list_display = ('name', 'description')
        search_fields = ('name', 'description')
        sortable = ('name',)

class WorkflowParameter(models.Model):

    """ Refers to an Actor property in a specific Workflow. Provides a
    way to assign a different value to a property without changing the
    original MoML file. Also specifies whether the property should be
    exposed to the user via the job submission form, and provides a
    verbose name and description to display on the form.

    workflow -- The Workflow which this property belongs to.
    property_id -- The unique reference used to access this property in
    the workflow.
    expse_to_user -- True if this property should be shown to the user
    on the job submission form.
    description -- A long description of this property.
    name -- The verbose name for this property.
    value -- The default value for this property.
    type -- The type of property. The type refers to the type of
    component used to present the property. The current supported types
    are: SELECT, INPUT, TEXT, CHECKBOX and FILE.
    """

    workflow = models.ForeignKey(Workflow)
    property_id = models.CharField(max_length=200, editable=False)
    expose_to_user = models.BooleanField()
    description = models.TextField()
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=1000)
    type = models.CharField(max_length=50)

    def __unicode__(self):
        return unicode('parameter "%s" for workflow "%s"' 
                       % (self.name, self.workflow.name))

    class Admin:
        list_display = ('workflow', 'property_id', 'name')

class Job(models.Model):

    """ A Job is a single execution of a Workflow.

    workflow -- The Workflow which was executed for this Job.
    owner -- The User whom submitted this Job.
    status -- The Job's current status.
    submission_date -- The date/time when the Job was submitted.
    start_date -- The date/time when the Job's status changed from
    QUEUED to RUNNING.
    end_date -- The date/time when the Job's status changed from RUNNING
    to either DONE or ERROR.
    name -- An optional name for the Job.
    description -- An optional description for the Job.
    """

    workflow = models.ForeignKey(Workflow)
    owner = models.ForeignKey(User)
    status = models.CharField(max_length=200)
    submission_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    name = models.CharField(max_length=200, null=True)
    description = models.TextField(null=True)

    def get_job_inputs(self):
        """ Returns all the JobInput objects associated with this Job.
        """
        return JobInput.objects.filter(job=self)

    def get_job_outputs(self):
        """ Returns all the JobOutput objects associated with this Job.
        """
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
        if self.name is None or self.name == '':
            return '%s Job' % self.workflow
        else:
            return self.name

    class Admin:
        list_display = ('workflow', 'submission_date', 'start_date',
                        'end_date', 'status', 'owner')
        search_fields = ('workflow__name', 'status',)
        list_filter = ('status',)
        date_hierarchy = 'submission_date'

    class Search:

        """ Class used by the kepler.portalviewshelper.SearchList class.
        """

        list_display = ('name', 'workflow', 'status', 'submission_date',
                        'end_date')
        search_fields = ('workflow__name', 'status', 'name', 'description')
        sortable = ('workflow__name',)

class JobInput(models.Model):

    """ When a Job is submitted, all the inputs that are assigned via
    WorkflowParameter objects are saved as JobInputs. They exist solely
    for record keeping purposes.

    job -- The Job which this belongs to.
    parameter -- the WorkflowParameter which this refers to.
    value -- the value which the WorkflowParameter was set to for the
    Job.
    """

    job = models.ForeignKey(Job)
    parameter = models.ForeignKey(WorkflowParameter)
    value = models.TextField()

    class Admin:
        pass

class JobOutput(models.Model):

    """ As a job runs, some actors may produce output. This output is
    captured via ReplacementActors and stored in a file. A JobOutput is
    a reference to this file with additional metadata.

    job -- The Job which produced this output.
    name -- The name of the output, generally the name of the Actor
    which produced it.
    type -- The type of output.
    file -- The file which holds the output.
    creation_date -- The date/time when the output was created.
    """

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

