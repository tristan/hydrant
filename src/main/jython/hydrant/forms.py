from django.db import models
from models import *
from django.newforms import ModelForm, Form
from django.newforms.fields import CharField, BooleanField
from django.newforms.widgets import RadioSelect, RadioFieldRenderer

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

class AddUserForm(Form):
    username = CharField(label='Username')
    has_edit = BooleanField(label='Can edit this Workflow', initial=False)
    has_view = BooleanField(label='Can see this Workflow', initial=True)
