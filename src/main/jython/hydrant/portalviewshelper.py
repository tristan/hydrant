from kepler.workflow.cache import *
from django.http import Http404
from django.utils.encoding import force_unicode, smart_str
from django.forms.forms import BaseForm
from django.utils.datastructures import SortedDict
from django import forms
from models import *
from django.db import models
from django.db.models.query import QuerySet
from django.db.models.fields import FieldDoesNotExist
import operator, traceback, os
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models.query import Q
from django.forms import widgets
from django.utils.text import capfirst
from django.contrib.auth.models import User
from settings import STORAGE_ROOT
from django.utils.safestring import mark_safe

def build_crumbs_from_path(current_name, path):
    """ Builds a list of breadcrumbs for traversing through Workflows with Composite Actors.

    Keyword arguments:
    current_name -- the name to present as the current view's name.
    path -- the path to the current view.
    """
    p = path.split('/')
    crumbs = []
    if len(p) > 1:
        crumbs.append({'name': current_name, 'path': '%s/' % '/'.join(['..' for j in range(len(p)-1)])})
        q = p[1:]
        size = len(q)-1
        for i in range(size):
            crumbs.append({'name': q[i], 'path': '%s/' % '/'.join(['..' for j in range(size-i)])})
    return crumbs or ['']

def generate_parameters_form(workflow, model, path_to_actor):
    """ This generates a Django forms class which can be used to
    instantiate an instance of a form containing all the properties of
    the specified actor.

    Keyword attributes:
    workflow -- the Workflow object for which to generate the form
    model -- an entity proxy object (EntityProxy)
    path_to_actor -- the path to the actor from the proxy object for
    which the properties form should be generated.
    """
    properties = model.get_properties(path_to_actor)
    field_list = []
    formfield_callback = lambda f, l, i: f.formfield(label=l, initial=i)
    for p in properties:
        try:
            wfp = WorkflowParameter.objects.get(workflow=workflow, property_id=p['id'])
            p['name'] = wfp.name
            p['value'] = wfp.value
            expose_to_user = wfp.expose_to_user
            property_description = wfp.description
        except:
            expose_to_user = False
            property_description = ''
        field_list.append(('%s_name' % p['id'], forms.CharField(initial=p['name'], label='Name')))
        thistype = p.get('type', 'INPUT')
        field_list.append(('%s_type' % p['id'], forms.ChoiceField(initial=thistype, label='Type', choices=(('INPUT','INPUT'),('TEXT','TEXT'),('FILE','FILE'),('CHECKBOX','CHECKBOX'),('SELECT','SELECT')))))
        if thistype == 'TEXT':
            field_list.append(('%s_value' % p['id'], forms.CharField(max_length=1000, initial=p['value'], label='Value', widget=forms.Textarea)))
        elif thistype == 'INPUT':
            field_list.append(('%s_value' % p['id'], forms.CharField(initial=p['value'], label='Value')))
        elif thistype == 'CHECKBOX':
            try:
                p['value'] = eval(capfirst(p['value']))
            except:
                if not isinstance(p['value'], bool):
                    print 'WARNING, EVAL ON CHECKBOX FAILED: %s (%s)' % (p['value'], type(p['value']))
            field_list.append(('%s_value' % p['id'], forms.BooleanField(initial=p['value'], label='Value', required=False)))
        elif thistype == 'SELECT':
            choices = tuple([(i, i) for i in p['choices']])
            if '"' in p['value']:
                p['value'] = eval(p['value'])
            field_list.append(('%s_value' % p['id'], forms.ChoiceField(initial=p['value'], label='Value', choices=choices)))
        elif thistype == 'FILE':
            field_list.append(('%s_value' % p['id'], forms.FileField(initial=p['value'], label='Value')))
        else:
            print 'WARNING, UNKNOWN TYPE: %s' % thistype
        field_list.append(('%s_expose' % p['id'], forms.BooleanField(initial=expose_to_user, label='Expose to User')))
        field_list.append(('%s_description' % p['id'], forms.CharField(max_length=1000, initial=property_description, label='Description', widget=forms.Textarea)))
    base_fields = SortedDict(field_list)
    return type(model.name + 'Form', (BaseForm,), {'base_fields': base_fields,})

def save_files(workflow, sfile):
    storedir = '%s/workflows/%s/' % (STORAGE_ROOT, workflow.id)
    fp = '%s%s' % (storedir , sfile['filename'])
    i = 0
    while os.path.exists(fp):
        fp = '%s%s%s' % (storedir, i, sfile['filename'])
        i += 1
    os.makedirs(storedir)
    f = open(fp, 'w')
    for i in sfile['content']:
        f.write(i)
    f.close()
    return fp

def save_parameters_from_post(workflow, post, files):
    """ Saves changes to the Workflow metadata stored in the Workflow
    model based of values passed in via a POST request.
    """
    f_value = None
    if files is not None:
        for i in files:
            print i
            f_value = save_files(workflow, files[i])
    ids = []
    for k in post.keys():
        s = k.split('_name')
        if len(s) > 1:
            ids.append(s[0])
    for id in ids:
        name = post.get('%s_name' % id, None)
        if f_value is None:
            value = post.get('%s_value' % id, None)
        else:
            value = f_value
        expose = post.get('%s_expose' % id, False)
        description = post.get('%s_description' % id, '')
        typ = post.get('%s_type' % id, 'INPUT')
        if typ == 'CHECKBOX':
            if value == None or value == '':
                value = 'false'
            else:
                value = 'true'
        wfp, created = WorkflowParameter.objects.get_or_create(workflow=workflow, property_id=id)
        wfp.name = name
        wfp.value = value or ''
        wfp.expose_to_user = expose
        wfp.description = description
        wfp.type = typ
        wfp.save()

def get_workflow_query_set(user):
    """ Does some funky messy creation of a complex filter, which
    selects all the workflows which a user has access to as well as all
    the public workflows, and makes sure each one hasn't been deleted.
    """
    qs = Q()
    for i in user.workflow_valid_users.all():
        qs |= Q(pk=i.pk)
    qs |= Q(public=True) | Q(owner=user)
    qs &= Q(deleted=False)
    return Workflow.objects.complex_filter(qs)

class RadioFieldRenderer(widgets.RadioFieldRenderer):
    def render(self):
        return mark_safe(u'\n'.join([u'%s'
                           % force_unicode(w) for w in self]))

