from django.db import models
from django.contrib.auth.models import User
import widgets
from kepler.workflow.proxy import EntityProxy, EntityProxyCache
from kepler.workflow import utils
import datetime, time, traceback
from django.core.mail import send_mail

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
    description = models.TextField(blank=True)
    public = models.CharField(max_length=3, default='OFF',
                              verbose_name='Who has access to this workflow?',
                              choices=(('ON', 'Anyone'),
                                       ('OFF', 'Only the people I specify'),
                                       )
                              )
    edit_permissions = models.ManyToManyField(User,
                                              verbose_name='Users who have edit rights', 
                                              blank=True, 
                                              filter_interface=models.HORIZONTAL,
                                              related_name='edit_permissions',
                                              )
    view_permissions = models.ManyToManyField(User,
                                              verbose_name='Users who can view', 
                                              blank=True, 
                                              filter_interface=models.HORIZONTAL,
                                              related_name='view_permissions',
                                              )
    deleted = models.BooleanField(default=False,)

    def all_permitted_users(self):
        return (self.edit_permissions.all() | self.view_permissions.all()).distinct()

    def has_view_permission(self, user):
        return (user in self.view_permissions.all() or
                user == self.owner or
                self.public == 'ON'
                )

    def has_edit_permission(self, user):
        return (user in self.edit_permissions.all() or
                user == self.owner
                )

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

    def parse_moml(self):
        try:
            utils.parse_moml(self.get_moml_file_filename())
            return True
        except:
            traceback.print_exc()
            return False

    def get_proxy_object(self, forexec=False):
        """ Returns a kepler.workflow.proxy.EntityProxy object which
        proxies this Workflow.
        """
        try:
            return EntityProxyCache.get_proxy(self, forexec)
        except:
            import StringIO
            f = StringIO.StringIO()
            traceback.print_exc(file=f)
            f.seek(0)
            self.error = f.read()
            f.close()
            return None

    def get_average_run_time(self):
        jobs = Job.objects.filter(workflow=self, status='DONE')
        if len(jobs) > 0:
            tm = 0
            for j in jobs:
                start = time.mktime(j.start_date.timetuple())
                end = time.mktime(j.end_date.timetuple())
                tm += (end - start)
            tm = (tm / len(jobs))
            return tm
        else:
            return None

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
    status = models.CharField(max_length=200,default='NEW')
    creation_date = models.DateTimeField(auto_now_add=True)
    submission_date = models.DateTimeField(null=True)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    name = models.CharField(max_length=200, null=True)
    description = models.TextField(null=True)

    def get_eta(self):
        if not self.start_date:
            return 'unknown'
        avg = self.workflow.get_average_run_time()
        if avg == None:
            return 'unknown'
        start = time.mktime(self.start_date.timetuple())
        return datetime.datetime.fromtimestamp(start + avg)

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
        pass

    class Meta:

        """ Class used by the kepler.portalviewshelper.SearchList class.
        """
        ordering = ('name',)

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
    #           URI
    file = models.CharField(max_length=200)
    creation_date = models.DateTimeField(auto_now_add=True)

    class Admin:
        list_display = ('creation_date', 'job', 'name', 'type', 'file')

class Message(models.Model):
    """ This model stores all the messages sent to a user

    user -- The user which the message if for.
    date -- The date the message was created.
    source -- The source of the message. i.e. Job or User
    title -- The title of the message
    text -- The contents of the message
    
    """

    fromuser = models.ForeignKey(User, related_name='fromuser')
    touser = models.ForeignKey(User, related_name='touser')
    date = models.DateTimeField(auto_now_add=True)
    verb = models.CharField(blank=True,max_length=200)
    private = models.BooleanField(default=True)
    text = models.TextField()

    def workflow(self):
        if self.is_workflow():
            return self.workflowmessage.workflow
        return None
    def job(self):
        if self.is_job():
            return self.jobmessage.job

    def subject(self):
        if self.is_user():
            return self.usermessage.subject

    def is_user(self):
        try:
            self.usermessage
            return True
        except:
            return False

    def is_workflow(self):
        try:
            self.workflowmessage
            return True
        except:
            return False

    def is_job(self):
        try:
            self.jobmessage
            return True
        except:
            return False

    class Admin:
        pass
    
def get_all_messages():
    msgs = Message.objects.all()
    return msgs

def get_all_messages_related_to_user(user):
    return (
        Message.objects.filter(touser=user) |
        Message.objects.filter(fromuser=user) |
        Message.objects.filter(touser=get_system_user(), private=False) |
        Message.objects.filter(fromuser=get_system_user(), private=False)
        )

def get_all_messages_for_user(user):
    msgs = Message.objects.filter(touser=user)
    return msgs

def get_all_messages_from_user(user):
    msgs = Message.objects.filter(fromuser=user)
    return msgs

class UserMessage(models.Model):
    subject = models.CharField(max_length=200)
    message = models.OneToOneField(Message)

    def save(self):
        super(UserMessage, self).save()
        profile, created = UserProfile.objects.get_or_create(user=self.message.touser)
        if profile.email_messages == True:
            try:
                send_mail('%s send you a message' % (self.message.fromuser),
                          'Subject: %s\n\n%s' % (self.subject, self.message.text),
                          self.message.fromuser.email,
                          [self.message.touser.email],)
            except:
                traceback.print_exc()
    
class JobMessage(models.Model):
    job = models.ForeignKey(Job)
    message = models.OneToOneField(Message)
    class Admin:
        pass

    def save(self):
        super(JobMessage, self).save()
        profile, created = UserProfile.objects.get_or_create(user=self.message.touser)
        if profile.email_job == True:
            try:
                send_mail('your job is now %s' % (self.job.status.lower()),
                          self.message.text,
                          'noreply@hydrant',
                          [self.message.touser.email],)
            except:
                traceback.print_exc()

class WorkflowMessage(models.Model):
    workflow = models.ForeignKey(Workflow)
    message = models.OneToOneField(Message)
    class Admin:
        pass

class Comment(models.Model):
    fromuser = models.ForeignKey(User, related_name='commenton')
    date = models.DateTimeField(auto_now_add=True)
    text = models.TextField()

class JobComment(Comment):
    job = models.ForeignKey(Job)

class WorkflowComment(Comment):
    workflow = models.ForeignKey(Workflow)
    
class UserProfile(models.Model):

    """ This model contains additional information about a User

    user -- The user which this info relates to.
    twitter -- The user's twitter id.
    """

    user = models.ForeignKey(User)

    company = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=200, blank=True)

    email_job = models.BooleanField()
    email_workflow = models.BooleanField()
    email_messages = models.BooleanField()
    email_comments = models.BooleanField()

def get_system_user():
    try:
        u = User.objects.get(username='system')
    except:
        u = User(username='system')
        u.is_active = 0
        u.save()
    return u
