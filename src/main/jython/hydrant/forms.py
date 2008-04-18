from django.db import models
from models import *
from django.newforms import ModelForm, Form, ValidationError
from django.newforms.fields import *
from django.newforms.widgets import RadioSelect, RadioFieldRenderer, PasswordInput, Textarea
from kepler.workflow import utils
import traceback

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
            utils.validate_moml(self['moml_file'].data['content'])
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


SEARCH_ORDER_CHOICES = (('ASC','ascending'),
                        ('DSC','decending'),
                        )
class SearchForm(Form):
    search_term = CharField(max_length=200)
    search_comments = BooleanField(initial=True)
    search_names = BooleanField(initial=True)
    search_users = BooleanField(initial=True)
    search_descriptions = BooleanField(initial=True)
    sort_order = CharField(
        widget=RadioSelect(
        renderer=RadioFieldRenderer,
        choices=SEARCH_ORDER_CHOICES,
        ),
        initial='ASC',
        )

JOB_SEARCH_ORDER_CHOICES = (('creation_date','Creation Date'),
                            ('submission_date','Submission Date'),
                            ('start_date','Start Date'),
                            ('ETA','Time Remaining'),
                            ('end_date','End Date'),
                            ('workflow','Workflow'),
                            ('owner','Owner'),
                            )
class JobSearchForm(SearchForm):
    sort_by = ChoiceField(choices=JOB_SEARCH_ORDER_CHOICES,initial='creation_date')

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
        if self['search_comments'].data == 'on':
            url += '&search_comments=on'
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
        if self['search_comments'].data == 'on':
            url += '&search_comments=on'
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
                'email_comments',
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
    
