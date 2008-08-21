import os
import traceback

from django.db import models
from django.forms import ModelForm, Form, ValidationError
from django.forms.fields import *
from django.forms.widgets import RadioSelect, RadioFieldRenderer, PasswordInput, Textarea
from django.core.validators import alnum_re

from django.contrib.auth.models import User
from models import *
from kepler.workflow import utils
from settings import STORAGE_ROOT

class EditWorkflowForm(ModelForm):
    public = CharField(
        widget=RadioSelect(
        renderer=RadioFieldRenderer,
        choices=Workflow._meta.get_field('public').choices,
        ),
        label='Who has access to this workflow?',
        )

    class Meta:
        model = Workflow
        fields=('name', 'description', 'public')

class UploadWorkflowForm(ModelForm):
    public = CharField(
        widget=RadioSelect(
        renderer=RadioFieldRenderer,
        choices=Workflow._meta.get_field('public').choices,
        ),
        label='Who has access to this workflow?',
        initial='OFF',
        )

    def validate_moml(self):
        try:
            a = self['moml_file'].data
            s = ''.join([i for i in a.chunks()])
            utils.validate_moml(s)
            return True
        except:
            traceback.print_exc()
            self.errors['moml_file'] = [u'Workflow validation failed.']
            return False
    
    class Meta:
        model = Workflow
        fields=('moml_file', 'name', 'description', 'public')

class AddUserForm(Form):
    username = CharField(label='Username')
    has_edit = BooleanField(label='Can edit this Workflow', initial=False)
    has_view = BooleanField(label='Can see this Workflow', initial=True)

class JobPermissionsForm(ModelForm):
    public = CharField(
        widget=RadioSelect(
        renderer=RadioFieldRenderer,
        choices=Job._meta.get_field('public').choices,
        ),
        label='Who can view this job?',
        initial='OFF',
        )
    username = CharField(label='Username')

    class Meta:
        model = Job
        fields = ('public',)

SEARCH_ORDER_CHOICES = (('ASC','ascending'),
                        ('DSC','decending'),
                        )
class SearchForm(Form):
    search_term = CharField(max_length=200)
    #search_comments = BooleanField(initial=True)
    search_names = BooleanField(initial=True)
    search_users = BooleanField(initial=True)
    search_descriptions = BooleanField(initial=True)
    sort_order = CharField(
        widget=RadioSelect(
        renderer=RadioFieldRenderer,
        choices=SEARCH_ORDER_CHOICES,
        ),
        initial='DSC',
        )

JOB_SEARCH_ORDER_CHOICES = (('last_modified','Last Modified'),
                            ('creation_date','Creation Date'),
                            ('submission_date','Submission Date'),
                            ('start_date','Start Date'),
                            ('ETA','Time Remaining'),
                            ('end_date','End Date'),
                            ('workflow','Workflow'),
                            ('owner','Owner'),
                            )
class JobSearchForm(SearchForm):
    sort_by = ChoiceField(choices=JOB_SEARCH_ORDER_CHOICES,initial='last_modified')

    def get_results(self):
        results = Job.objects.get_empty_query_set()
        term = self['search_term'].data
        if self['search_descriptions'].data == 'on':
            r = Job.objects.filter(description__icontains=term)
            for j in r:
                if hasattr(j, 'matches'):
                    j.matches.append('description')
                else:
                    j.matches = ['description']
            results |= r
        if self['search_names'].data == 'on':
            r = Job.objects.filter(name__icontains=term)
            for j in r:
                if hasattr(j, 'matches'):
                    j.matches.append('name')
                else:
                    j.matches = ['name']
            results |= r
        if self['search_users'].data == 'on':
            r = Job.objects.filter(owner__username__icontains=term)
            r |= Job.objects.filter(owner__first_name__icontains=term)
            r |= Job.objects.filter(owner__last_name__icontains=term)
            for j in r:
                if hasattr(j, 'matches'):
                    j.matches.append('owner')
                else:
                    j.matches = ['owner']
            results |= r
        if self['sort_by'].data == 'ETA':
            pass
        else:
            results = results.order_by('%s%s' % (
                self['sort_order'].data == 'DSC' and '-' or '',
                self['sort_by'].data
                )
            )
        return results
    
    def get_url(self):
        url = '?'
        url += 'search_term=%s' % self['search_term'].data
        if self['search_descriptions'].data == 'on':
            url += '&search_descriptions=on'
        if self['search_names'].data == 'on':
            url += '&search_names=on'
        if self['search_users'].data == 'on':
            url += '&search_users=on'
        url += '&sort_by=%s' % self['sort_by'].data
        url += '&sort_order=%s' % self['sort_order'].data
        return url
        
        
WORKFLOW_SEARCH_ORDER_CHOICES = (('created','Creation Date'),
                                 ('owner','Owner'),
                                 )
class WorkflowSearchForm(SearchForm):
    sort_by = ChoiceField(choices=WORKFLOW_SEARCH_ORDER_CHOICES,initial='created')

    def get_results(self):
        results = Workflow.objects.get_empty_query_set()
        term = self['search_term'].data
        if self['search_descriptions'].data == 'on':
            r = Workflow.objects.filter(description__icontains=term)
            for j in r:
                if hasattr(j, 'matches'):
                    j.matches.append('description')
                else:
                    j.matches = ['description']
            results |= r
        if self['search_names'].data == 'on':
            r = Workflow.objects.filter(name__icontains=term)
            for j in r:
                if hasattr(j, 'matches'):
                    j.matches.append('name')
                else:
                    j.matches = ['name']
            results |= r
        if self['search_users'].data == 'on':
            r = Workflow.objects.filter(owner__username__icontains=term)
            r |= Workflow.objects.filter(owner__first_name__icontains=term)
            r |= Workflow.objects.filter(owner__last_name__icontains=term)
            for j in r:
                if hasattr(j, 'matches'):
                    j.matches.append('owner')
                else:
                    j.matches = ['owner']
            results |= r
        if self['sort_by'].data == 'ETA':
            pass
        else:
            results = results.order_by('%s%s' % (
                self['sort_order'].data == 'DSC' and '-' or '',
                self['sort_by'].data
                )
            )
        return results
    
    def get_url(self):
        url = '?'
        url += 'search_term=%s' % self['search_term'].data
        if self['search_descriptions'].data == 'on':
            url += '&search_descriptions=on'
        if self['search_names'].data == 'on':
            url += '&search_names=on'
        if self['search_users'].data == 'on':
            url += '&search_users=on'
#        if self['search_comments'].data == 'on':
#            url += '&search_comments=on'
        url += '&sort_by=%s' % self['sort_by'].data
        url += '&sort_order=%s' % self['sort_order'].data
        return url
        
        
class UserInfoForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(UserInfoForm, self).__init__(*args, **kwargs)
        self.fields['first_name'] = CharField(max_length=50,
                                              initial=self.instance.user.first_name)
        self.fields['last_name'] = CharField(max_length=50,
                                             initial=self.instance.user.last_name)
        self.fields['email'] = EmailField(initial=self.instance.user.email)

    def save(self, *args, **kwargs):
        if kwargs.has_key('commit'):
            commit = kwargs['commit']
            kwargs['commit'] = False
        else:
            commit = True
        profile = super(UserInfoForm, self).save(*args, **kwargs)
        profile.user.first_name = self['first_name'].data
        profile.user.last_name = self['last_name'].data
        profile.user.email = self['email'].data
        if commit:
            profile.user.save()
            profile.save()
        return profile

    class Meta:
        model = UserProfile
        fields=('company',
                'city',
                'country',
                'email_job',
                'email_workflow',
                'email_messages',
                )

class PasswordChangeForm(Form):

    old_password = CharField(label='Old password',
                             max_length=200,
                             widget=PasswordInput())
    new_password1 = CharField(label='New password',
                              max_length=200,
                              widget=PasswordInput())
    new_password2 = CharField(label='Confirm new password',
                              max_length=200,
                              widget=PasswordInput())

    def __init__(self, user, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        self.user = user

    def clean_old_password(self):
        if not self.user.check_password(self.cleaned_data['old_password']):
            raise ValidationError('password is incorrect')

    def clean(self):
        try:
            if self.cleaned_data['new_password1'] != self.cleaned_data['new_password2']:
                raise ValidationError('passwords don\'t match')
        except KeyError:
            pass
        return self.cleaned_data

    def save(self):
        self.user.set_password(self.cleaned_data['new_password1'])
        self.user.save()
        return self.user


class CommentForm(Form):
    subject = CharField(max_length=200)
    message = CharField(max_length=2048,
                        widget=Textarea(),
                        )


def generate_job_fields(form, workflow, job=None):
    parameters = workflow.get_exposed_parameters()
    for p in parameters:
        if job != None:
            try:
                ji = JobInput.objects.get(job=job,parameter=p)
                p.value = ji.value
            except:
                pass
        if p.type == 'TEXT':
            form.fields['%s' % p.property_id] = CharField(
                max_length=1000,
                initial=p.value,
                label=p.name,
                help_text=p.description,
                widget=Textarea
                )
        elif p.type == 'CHECKBOX':
            form.fields['%s' % p.property_id] = BooleanField(
                initial=eval(capfirst(p.value)),
                label=p.name,
                help_text=p.description
                )
        elif p.type == 'SELECT':
            m = workflow.get_model()
            actor = p.property_id.split('.')[2]
            choices = tuple([(i, i) for i in [i for i in m.get_properties([actor]) if i['id'] == p.property_id][0]['choices']])
            if '"' in p.value:
                p.value = eval(p.value)
                form.fields['%s' % p.property_id] = ChoiceField(
                    initial=p.value,
                    label=p.name,
                    choices=choices,
                    help_text=p.description
                    )
        elif p.type == 'FILE':
            form.fields['%s' % p.property_id] = FileField(
                #initial=p.value, # cannot display initial in file field
                label=p.name,
                help_text=p.description
                )
            # this is a hack to allow a job to be saved without yet putting
            # in any file data. this however, breaks form validation
            form.fields['%s' % p.property_id].clean = lambda s,a: None
        elif p.type == 'INPUT':
            form.fields['%s' % p.property_id] = CharField(
                initial=p.value,
                label=p.name,
                help_text=p.description
                )
        else:
            raise 'invalid parameter type for property %s: type "%s" unknown' % ( p.property_id, p.type)
                
class JobPreviewForm(ModelForm):
    class Meta:
        model = Workflow
        exclude = ('moml_file','name','owner','created','description','public',
                   'edit_permissions','view_permissions','deleted')

    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        if hasattr(self, 'instance'):
            generate_job_fields(self, self.instance)


BINARY_CONTENT_TYPES = ('application', 'image',)
class JobCreationForm(ModelForm):
    class Meta:
        model = Job
        fields=('name', 'description')

    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        # dodgy hack to remove validation from description field
        self.fields['description'].clean = lambda s: s
        if hasattr(self, 'instance'):
            generate_job_fields(self, self.instance.workflow, self.instance)
            
    def save(self, *args, **kwargs):
        ret = super(ModelForm, self).save(*args, **kwargs)
        if hasattr(self, 'instance'):
            if self.files.keys() != []:
                dirname = '%s/jobs/%s/input' % (STORAGE_ROOT, self.instance.pk)
                try:
                    os.makedirs(dirname)
                except:
                    if not os.path.exists(dirname):
                        raise
            parameters = self.instance.workflow.get_exposed_parameters()
            for p in parameters:
                if p.property_id in self.data.keys():
                    value = self.data.get('%s' % p.property_id)
                elif p.property_id in self.files.keys():
                    form_file = self.files.get(p.property_id)
                    if True in map(lambda a: a in form_file.content_type, BINARY_CONTENT_TYPES):
                        binary = True
                    else:
                        binary = False
                    filename = '%s/%s' % (dirname, form_file.name)
                    stored_file = open(filename, 'w%s' % (binary and 'b' or ''))
                    stored_file.write(form_file.read())
                    stored_file.close()
                    value = filename
                else:
                    value = p.value
                if p.type == 'CHECKBOX':
                    # workaround to turn off checkboxes
                    if p.expose_to_user == True and p.property_id not in self.data.keys():
                        value = 'false'
                    elif value == 'on':
                        value = 'true'
                ji, created = JobInput.objects.get_or_create(job=self.instance, parameter=p)
                ji.value = value
                ji.save()
        return ret

class UserField(CharField):
    def clean(self, value):
        super(UserField, self).clean(value)
        try:
            User.objects.get(username=value)
            raise ValidationError("Someone is already using this username. Please pick an other.")
        except User.DoesNotExist:
            return value

class SignupForm(Form):
    username = UserField(max_length=30)
    password = CharField(widget=PasswordInput())
    password2 = CharField(widget=PasswordInput(), label="Repeat your password")
    email = EmailField()
    email2 = EmailField(label="Repeat your email")

    first_name = CharField(max_length=30, required=False)
    last_name = CharField(max_length=30, required=False)
    company = CharField(max_length=200, required=False)
    city = CharField(max_length=200, required=False)
    country = CharField(max_length=200, required=False)

    def clean_username(self):
        if alnum_re.search(self.data['username']):
            return self.data['username']
        else:
            raise ValidationError("This value must contain only letters, numbers and underscores.")

    def clean_email(self):
        if self.data['email'] != self.data['email2']:
            raise ValidationError('Emails are not the same')
        if self.data['email'] != '':
            try:
                User.objects.get(email=self.data['email'])
                raise ValidationError("A user is already registered with this email address.")
            except User.DoesNotExist:
                pass
        return self.data['email']
    def clean_email2(self):
        if self.data['email'] != self.data['email2']:
            raise ValidationError('')
        return self.data['email2']

    def clean_password(self):
        if self.data['password'] != self.data['password2']:
            raise ValidationError('Passwords are not the same')
        return self.data['password']
    def clean_password2(self):
        if self.data['password'] != self.data['password2']:
            raise ValidationError('')
        return self.data['password2']
    
    def clean(self,*args, **kwargs):
        self.clean_email()
        self.clean_password()
        return super(SignupForm, self).clean(*args, **kwargs)

    def save(self, commit=True):
        if commit == False:
            raise 'Cannot save without commit'
        u = User(username=self.cleaned_data['username'],
                 email=self.cleaned_data['email'],
                 first_name=self.cleaned_data['first_name'],
                 last_name=self.cleaned_data['last_name'],
                 )
        u.set_password(self.cleaned_data['password'])
        u.save()
        p = UserProfile(user=u,
                        company=self.cleaned_data['company'],
                        city=self.cleaned_data['city'],
                        country=self.cleaned_data['country'],
                        )
        p.save()
        return (u, p)
