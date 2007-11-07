from workflow.cache import *
from django.http import Http404
#from forms import ParameterForm
from django.newforms import form_for_model
from django.utils.encoding import force_unicode, smart_str
from django.newforms.forms import BaseForm, SortedDictFromList
from django import newforms as forms
from models import *
from django.db import models
from django.db.models.query import QuerySet
import operator, traceback
from django.core.paginator import ObjectPaginator
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse

def build_crumbs_from_path(current_name, path):
    """
    current_name
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
    parameters = workflow.get_exposed_parameters()
    field_list = []
    formfield_callback = lambda f, l, i, h: f.formfield(label=l, initial=i, help_text=h)
    if len(parameters) == 0:
        return None
    for p in parameters:
        field = models.CharField(max_length=200, name='%s' % p.property_id)
        field_list.append((field.name, formfield_callback(field, p.name, p.value, p.description)))
    base_fields = SortedDictFromList(field_list)
    return type('ExposedParametersForm', (BaseForm,), {'base_fields': base_fields,})

def setup_job_parameters_from_post(job, post):
    parameters = job.workflow.get_all_parameters()
    for p in parameters:
        if p.property_id in post.keys():
            value=post.get('%s' % p.property_id)
        else:
            value = p.value
        ji = JobInput(job=job, parameter=p, value=value)
        ji.save()

def generate_parameters_form(workflow, model, path_to_actor):
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
        name = models.CharField(max_length=200, name='%s_name' % p['id'])
        value = models.CharField(max_length=200, name='%s_value' % p['id'])
        expose = models.BooleanField(name='%s_expose' % p['id'])
        description = models.TextField(name='%s_description' % p['id'])
        field_list.append((name.name, formfield_callback(name, 'Name', p['name'])))
        field_list.append((value.name, formfield_callback(value, 'Value', p['value'])))
        field_list.append((expose.name, formfield_callback(expose, 'Expose to User', expose_to_user)))
        field_list.append((description.name, formfield_callback(description, 'Description', property_description)))
    base_fields = SortedDictFromList(field_list)
    return type(path_to_actor[-1] + 'Form', (BaseForm,), {'base_fields': base_fields,})

def save_parameters_from_post(workflow, post):
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
        wfp, created = WorkflowParameter.objects.get_or_create(workflow=workflow, property_id=id)
        wfp.name = name
        wfp.value = value
        wfp.expose_to_user = expose
        wfp.description = description
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
    def __init__(self, request, model, view_url):
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

        # do ordering
        self.order_field, self.order_type = model.Search.list_display[0], 'asc'
        if ORDER_VAR in self.params:
            try:
                order_field = self.params[ORDER_VAR]
                try:
                    model._meta.get_field(order_field)
                except models.FieldDoesNotExist:
                    traceback.print_exc()
                    pass # invalid field name, ignore
                else:
                    self.order_field = order_field
                    if ORDER_TYPE_VAR in self.params and self.params[ORDER_TYPE_VAR] in ('asc', 'desc'):
                        self.order_type = self.params[ORDER_TYPE_VAR]
            except (IndexError, ValueError):
                pass # Invaid ordering specified.

        self.query = request.GET.get(SEARCH_VAR, '')
        qs = model._default_manager.get_query_set()
        lookup_params = self.params.copy()
        for i in (ALL_VAR, ORDER_VAR, ORDER_TYPE_VAR, SEARCH_VAR):
            if i in lookup_params:
                del lookup_params[i]
        for key, value in lookup_params.items():
            if not isinstance(key, str):
                del lookup_params[key]
                lookup_params[smart_str(key)] = value

        print lookup_params
        qs = qs.filter(**lookup_params)

        for field_name in model.Search.list_display:
            try:
                f = model._meta.get_field(field_name)
            except models.FieldDoesNotExist:
                pass
            else:
                if isinstance(f.rel, models.ManyToOneRel):
                    qs = qs.select_related()
                    break

        # do ordering stuff
        lookup_order_field = self.order_field
        try:
            f = model._meta.get_field(self.order_field, many_to_many=False)
        except models.FieldDoesNotExist:
            pass
        else:
            if isinstance(f.rel, models.OneToOneRel):
                pass
            elif isinstance(f.rel, models.ManyToOneRel):
                rel_ordering = f.rel.to._meta.ordering and f.rel.to._meta.ordering[0] or f.rel.to._meta.pk.column
                lookup_order_field = '%s.%s' % (f.rel.to._meta.db_table, rel_ordering)

        qs = qs.order_by((self.order_type == 'desc' and '-' or '') + lookup_order_field)

        # Apply keyword searches.
        def construct_search(field_name):
            print 'FIELD_NAME=%s' % field_name
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
        else:
            full_result_count = model._default_manager.count()

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
        """
        returns the real field, needed for cases where field being refered to is a 
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
