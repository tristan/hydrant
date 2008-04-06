from kepler.workflow.cache import *
from django.http import Http404
from django.newforms import form_for_model
from django.utils.encoding import force_unicode, smart_str
from django.newforms.forms import BaseForm
from django.utils.datastructures import SortedDict
from django import newforms as forms
from models import *
from django.db import models
from django.db.models.query import QuerySet
from django.db.models.fields import FieldDoesNotExist
import operator, traceback, os
from django.core.paginator import ObjectPaginator
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models.query import Q
from django.newforms import widgets
from django.utils.text import capfirst
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

def generate_job_submission_form(workflow):
    """ Generates a Django newforms class which can be used to
    instantiate a Form containing all the exposed parameters linked
    to the specified workflow.
    """
    parameters = workflow.get_exposed_parameters()
    field_list = []
    formfield_callback = lambda f, l, i, h: f.formfield(label=l, initial=i, help_text=h)
    if len(parameters) == 0:
        return None
    for p in parameters:
        if p.type == 'TEXT':
            field_list.append(('%s' % p.property_id, forms.CharField(max_length=1000, initial=p.value, label=p.name, help_text=p.description, widget=forms.Textarea)))
        elif p.type == 'CHECKBOX':
            field_list.append(('%s' % p.property_id, forms.BooleanField(initial=eval(capfirst(p.value)), label=p.name, help_text=p.description)))
        elif p.type == 'SELECT':
            m = workflow.get_model()
            actor = p.property_id.split('.')[2]
            choices = tuple([(i, i) for i in [i for i in m.get_properties([actor]) if i['id'] == p.property_id][0]['choices']])
            if '"' in p.value:
                p.value = eval(p.value)
            field_list.append(('%s' % p.property_id, forms.ChoiceField(initial=p.value, label=p.name, choices=choices, help_text=p.description)))
        elif p.type == 'FILE':
            field_list.append(('%s' % p.property_id, forms.FileField(initial=p.value, label=p.name, help_text=p.description)))
        else:
            field_list.append(('%s' % p.property_id, forms.CharField(initial=p.value, label=p.name, help_text=p.description)))
    base_fields = SortedDict(field_list)
    return type('ExposedParametersForm', (BaseForm,), {'base_fields': base_fields,})

BINARY_CONTENT_TYPES = ['application', 'image']
def setup_job_parameters_from_post(job, post, files={}):
    """ Creates a number of JobInput entries based on the values
    submitted from a job submission form.
    """
    if not isinstance(files, dict):
        print 'NOT PROCESSING FILES: %s' % files
        files = {}
    if files.keys() != []:
        dirname = '%s/jobs/%s/input' % (STORAGE_ROOT, job.pk)
        try:
            os.makedirs(dirname)
        except:
            if not os.path.exists(dirname):
                raise
    parameters = job.workflow.get_all_parameters()
    for p in parameters:
        if p.property_id in post.keys():
            value=post.get('%s' % p.property_id)
        elif p.property_id in files.keys():
            form_file = files.get(p.property_id)
            # checks for the existance of each string in BINARY_CONTENT_TYPES inside the content-type string
            # returning a list of Trues and Falses, if there is a True in the list, then one of the strings matched
            # and thus we know we're dealing with binary data
            if True in map(lambda a: a in form_file['content-type'], BINARY_CONTENT_TYPES):
                binary = True
            else:
                binary = False
            filename = '%s/%s' % (dirname, form_file['filename'])
            stored_file = open(filename, 'w%s' % (binary and 'b' or ''))
            stored_file.write(form_file['content'])
            stored_file.close()
            value = filename
        else:
            value = p.value
        if p.type == 'CHECKBOX':
            # workaround to turn off checkboxes
            if p.expose_to_user == True and p.property_id not in post.keys():
                value = 'false'
            elif value == 'on':
                value = 'true'
        ji = JobInput(job=job, parameter=p, value=value)
        ji.save()

def generate_parameters_form(workflow, model, path_to_actor):
    """ This generates a Django newforms class which can be used to
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
    return type(path_to_actor[-1] + 'Form', (BaseForm,), {'base_fields': base_fields,})

def save_parameters_from_post(workflow, post, files):
    """ Saves changes to the Workflow metadata stored in the Workflow
    model based of values passed in via a POST request.
    """
    if files is not None:
        print 'FILES! WOOOT!', files
    ids = []
    for k in post.keys():
        s = k.split('_name')
        if len(s) > 1:
            ids.append(s[0])
    for id in ids:
        name = post.get('%s_name' % id, None)
        value = post.get('%s_value' % id, None)
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
        wfp.value = value
        wfp.expose_to_user = expose
        wfp.description = description
        wfp.type = typ
        wfp.save()

# Changelist settings
ALL_VAR = 'all'
ORDER_VAR = 'o'
ORDER_TYPE_VAR = 'ot'
PAGE_VAR = 'p'
SEARCH_VAR = 'q'
IS_POPUP_VAR = 'pop'
ERROR_FLAG = 'e'

# Text to display within change-list table cells if the value is blank.
EMPTY_CHANGELIST_VALUE = '(None)'

MAX_SHOW_ALL_ALLOWED = 200

class SearchList(object):

    """ Based off django.contrib.admin.views.main.ChangeList, with some
    application specific changes.

    A lof of the functions have been rolled out into the constructor,
    and a few static choices have been embeded which need to be removed
    at some time.
    """

    def __init__(self, request, model, qs, view_url):
        try:
            self.page_num = int(request.GET.get(PAGE_VAR, 0))
        except ValueError:
            self.page_num = 0
        self.params = dict(request.GET.items())
        if PAGE_VAR in self.params:
            del self.params[PAGE_VAR]
        if ERROR_FLAG in self.params:
            del self.params[ERROR_FLAG]
        self.show_all = ALL_VAR in request.GET

        self.query = request.GET.get(SEARCH_VAR, '')
        # assume the model has a Search class, with a list_display list
        # property. default sorting uses the first entry in this list.
        self.order_field, self.order_type = model.Search.list_display[0], 'asc'

        full_result_count = len(qs)

        # Apply keyword searches.
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        if self.query:
            for bit in self.query.split():
                print 'BIT=%s' % bit
                or_queries = [models.Q(**{construct_search(field_name): bit}) for field_name in model.Search.search_fields]
                other_qs = QuerySet(model)
                if qs._select_related:
                    other_qs = other_qs.select_related()
                other_qs = other_qs.filter(reduce(operator.or_, or_queries))
                qs = qs & other_qs

        self.query_set = qs

        # TODO: make number of objects per page a setting
        max_per_page = 30
        paginator = ObjectPaginator(self.query_set, max_per_page)
        try:
            result_count = paginator.hits
        except:
            traceback.print_exc()
            raise IncorrectLookupParameters

        if isinstance(self.query_set._filters, models.Q) and not self.query_set._filters.kwargs:
            full_result_count = result_count

        can_show_all = result_count <= MAX_SHOW_ALL_ALLOWED
        multi_page = result_count > max_per_page

        if (self.show_all and can_show_all) or not multi_page:
            result_list = list(self.query_set)
        else:
            try:
                result_list = paginator.get_page(self.page_num)
            except InvalidPage:
                result_list = ()

        self.result_count = result_count
        self.full_result_count = full_result_count
        self.can_show_all = can_show_all
        self.multipage = multi_page
        self.paginator = paginator

        self.pagination_required = (not self.show_all or not self.can_show_all) and self.multipage
        if not self.pagination_required:
            page_range = []
        else:
            if paginator.pages <= 10:
                page_range = list(self.do_pagination(0, paginator.pages))
            else:
                ON_EACH_SIDE = 3
                ON_ENDS = 2
                page_range = []
                DOT = { 'dot': True }
                if self.page_num > (ON_EACH_SIDE + ON_ENDS):
                    page_range.extend(self.do_pagination(0, ON_EACH_SIDE - 1))
                    page_range.append(DOT);
                    page_range.extend(self.do_pagination(self.page_num - ON_EACH_SIDE, self.page_num + 1))
                else:
                    page_range.extend(self.do_pagination(0, self.page_num + 1))
                if self.page_num < (paginator.pages - ON_EACH_SIDE - ON_ENDS - 1):
                    page_range.extend(self.do_pagination(self.page_num + 1, self.page_num + ON_EACH_SIDE + 1))
                    page_range.append(DOT)
                    page_range.extend(self.do_pagination(paginator.pages - ON_ENDS, paginator.pages))
                else:
                    page_range.extend(self.do_pagination(self.page_num + 1, paginator.pages))

        self.pages = page_range

        self.filter_specs = []
        self.has_filters = False
        self.pk_attname = model._meta.pk.attname

        self.model = model
        self.view_url = view_url
        self.result_headers = list(self.result_headers())
        self.result_list = list(self.get_results(result_list))

    def get_table_ref(self, model, field_name):
        s = field_name.split('__')
        if len(s) == 1:
            return model._meta.get_field(field_name)
        else:
            return '%s.%s' % (model._meta.get_field(s[0]).rel.to._meta.db_table, '__'.join(s[1:]))

    def get_real_field(self, model, field_name):
        """ Returns the real field, needed for cases where field being refered to is a 
        field from the foreign key's table
        """
        s = field_name.split('__')
        if len(s) == 1:
            return model._meta.get_field(field_name)
        else:
            return self.get_real_field(model._meta.get_field(s[0]).rel.to, '__'.join(s[1:]))


    def do_pagination(self, start_page, num_of_pages):
        for i in range(start_page, num_of_pages):
            if i == self.page_num:
                yield { 'num': i+1, 'last_page': i == self.paginator.pages-1 }
            else:
                yield { 'num': i+1, 'last_page': i == self.paginator.pages-1, 'url': self.get_query_string({ PAGE_VAR: i }) }

    def get_results(self, result_list):
        for res in result_list:
            yield list(self.result_items(res))

    def result_items(self, result):
        first = True
        for field_name in self.model.Search.list_display:
            try:
                f = self.model._meta.get_field(field_name)
            except:
                traceback.print_exc()
                field_val = ''
            else:
                field_val = getattr(result, f.attname)
                if isinstance(f.rel, models.ManyToOneRel):
                    if field_val is not None:
                        field_val = getattr(result, f.name)
            if first:
                result_id = getattr(result, 'pk')
                first = False
                url = reverse(self.view_url, args=(result_id,))
                yield {'text': force_unicode(field_val), 'url': url }
            else:
                yield {'text': force_unicode(field_val)}

    def result_headers(self):
        for i, field_name in enumerate(self.model.Search.list_display):
            try:
                f = self.model._meta.get_field(field_name)
            except:
                traceback.print_exc()
            else:
                header = f.verbose_name

            if field_name == self.order_field:
                sorted = True
                order_type = {'asc': 'desc', 'desc': 'asc'}[self.order_type.lower()]
            else:
                order_type = 'asc'
                sorted = False

            yield { 'text': header,
                    'sortable': field_name != 'description',
                    'url': self.get_query_string({ORDER_VAR: i, ORDER_TYPE_VAR: order_type}),
                    'sorted': sorted,
                  }

    def get_query_string(self, new_params=None, remove=None):
        if new_params is None: new_params = {}
        if remove is None: remove = []
        p = self.params.copy()
        for r in remove:
            for k in p.keys():
                if k.startswith(r):
                    del p[k]
        for k, v in new_params.items():
            if k in p and v is None:
                del p[k]
            elif v is not None:
                p[k] = v
        return '?' + '&amp;'.join([u'%s=%s' % (k, v) for k, v in p.items()]).replace(' ', '%20')


class WorkflowList(SearchList):

    """ A SearchList specific to Workflows
    """

    def __init__(self, request, view_url):
        qs = get_workflow_query_set(request.user)
        SearchList.__init__(self, request, Workflow, qs, view_url)

class JobList(SearchList):

    """ A SearchList specific to Jobs
    """

    def __init__(self, request, view_url):
        qs = Job._default_manager.get_query_set()
        qs = qs.filter(owner=request.user)
        SearchList.__init__(self, request, Job, qs, view_url)

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

def upload_workflow_formfield_callback(field, **kwargs):
    """ Used to assign the FilteredSelectMultiple widget for
    ManyToManyField objects when generating a form.
    """
    if field.name == 'public':
        kwargs['widget'] = widgets.RadioSelect(choices=field.choices,
                                               renderer=RadioFieldRenderer)
    if field.name == 'description':
        kwargs['widget'] = widgets.Textarea({'rows':5})

    return field.formfield(**kwargs)

