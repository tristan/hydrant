import time, md5, traceback, copy, array, shutil, random

from django import oldforms #, template
from django.template.context import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from django.http import Http404, HttpResponseServerError, HttpResponse, HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.datastructures import FileDict
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist, PermissionDenied
from django.views.static import serve

#from pygments import highlight
#from pygments.lexers import XmlLexer
#from pygments.formatters import HtmlFormatter

from kepler.workflow.utils import validateMoML
from kepler.workflow.cache import open_workflow, open_workflow_from_object
from portalviewshelper import *
from models import *
from job import *
from settings import STORAGE_ROOT, MEDIA_ROOT
from django.newforms import form_for_model, form_for_instance
from django.utils.safestring import mark_safe

def intro(request):
    return render_to_response('kepler/intro.html', {'pic_no':random.randint(0,10)}, context_instance=RequestContext(request))

def hide_workflows(request, path):
    """ Used to hide the path to the workflow xml files from everyone
    """
    raise Http404

def welcome(request):
    """ Displays the welcome page
    """
    return render_to_response('index.html', context_instance=RequestContext(request))

def dashboard(request):
    """ Displays the users dashboard. Includes lists of the last five
    uploaded Workflows and Jobs.
    """
    workflows = [i for i in Workflow.objects.filter(public=True,deleted=False)]
    jobs = []
    if request.user.is_authenticated():
        workflows.extend([i for i in Workflow.objects.filter(owner=request.user,deleted=False) if i not in workflows])
        jobs = Job.objects.filter(owner=request.user).order_by('-submission_date')
        if len(jobs) > 5:
            jobs = jobs[:5]
    else:
        # set the test cookie, so that if the user decides to log in the login form actually works
        request.session.set_test_cookie()
    return render_to_response('kepler/dashboard.html', {'next': reverse('dashboard'), 'title': _('Dashboard'), 'workflows': workflows, 'jobs': jobs, }, context_instance=RequestContext(request))
dashboard = login_required(dashboard)

def upload_workflow(request):
    """ Handles uploading a Workflow. If a GET request is made, then
    return a page displaying the upload form. If a POST request is made,
    check the POST and FILES variables for Workflow details and store
    them.
    """
    WorkflowForm = form_for_model(Workflow, fields=('moml_file','name','public','description','valid_users'), formfield_callback=formfield_callback)
    if request.method == 'POST':
        print request.POST
        form = WorkflowForm(request.POST, request.FILES)
        if form.is_valid():
            messages = []
            workflow = form.save(commit=False)
            workflow.owner = request.user
            workflow.save()
            form.save_m2m()
            messages.append({'type':'MESSAGE', 'message':'The workflow "%s" was uploaded successfully' % workflow.name})
            for msg in messages:
                request.user.message_set.create(message=msg)
            return HttpResponseRedirect(reverse('workflow_view', args=(workflow.pk,)))
    else:
        form = WorkflowForm()
    return render_to_response('kepler/upload_workflow.html', {'title': _('Upload Workflow'), 'crumbs': [''], 'form': form.as_table() }, context_instance=RequestContext(request))
upload_workflow = login_required(upload_workflow)

def workflow(request, id):
    """ If a GET request, returns the page which displays a Workflow. If
    a POST request, checks the POST variables for Workflow metadata
    values and stores them for the specified workflow.
    """
    workflow = get_object_or_404(Workflow, pk=id)
    # check permissions
    if not workflow.public and workflow.owner != request.user and request.user not in workflow.valid_users.all():
        raise Http404
    PropertiesForm = form_for_instance(workflow, fields=('name','public','description','valid_users'), formfield_callback=formfield_callback)
    if request.method == 'POST':
        pform = PropertiesForm(request.POST)
        if pform.is_valid():
            workflow = pform.save()
            return HttpResponse('')
        else:
            job = Job(workflow=workflow, owner=request.user, status='NEW')
            job.save()
            setup_job_parameters_from_post(job, request.POST, hasattr(request, 'FILES') and request.FILES or None)
            queue_new_job(job)
            request.user.message_set.create(message={'type':'MESSAGE', 'message':'This job has been submitted. You should take the time to fill out a name and description for this job.'})
            return HttpResponseRedirect(reverse('job_details_view', args=(job.pk,)))
    else:
        if request.user.is_staff:
            pform = PropertiesForm()
        else:
            pform = None
    return render_to_response('kepler/view_workflow.html', {'crumbs': [{'name': 'Workflows', 'path': reverse('workflows')},], 'editable': request.user.is_staff, 'next': reverse('workflow_view', args=(id,)), 'title': _(workflow.name), 'workflow': workflow, 'properties_form': pform is None and '' or pform}, context_instance=RequestContext(request))

def model(request, path):
    """ Retrieves the dict representation of the entity refered to by
    path, and returns a web page which uses that dict to display a graph
    of the specified entity. Generally used by the Workflow view as an
    Ajax call.
    """
    p = path.split('/')
    w_id = p[0]
    model, workflow = open_workflow(request.user, w_id)
    # check permissions
    if not workflow.public and workflow.owner != request.user and request.user not in workflow.valid_users.all():
        raise Http404
    crumbs = build_crumbs_from_path(workflow.name, path)
    if len(p) > 1:
        name = p[-1]
    else:
        name = workflow.name
    props = reverse('parameters', args=(path,))
    return render_to_response('kepler/workflow_canvas.html', {'crumbs': crumbs, 'editable': request.GET.get('editable', False), 'next': reverse('model_view', args=(path,)), 'title': _(name), 'workflow': workflow, 'model': model.get_as_dict(p[1:]), 'parameters_url_base': props}, context_instance=RequestContext(request))

def job_form(request, id):
    """ Returns a page displaying the Job Submission Form
    """
    workflow = get_object_or_404(Workflow, pk=id)
    JobSubmissionForm = generate_job_submission_form(workflow)
    if JobSubmissionForm is not None:
        params = JobSubmissionForm()
    else:
        params = None
    return render_to_response('kepler/parameters_form.html', { 'workflow': workflow, 'parameters': params }, context_instance=RequestContext(request))

def properties(request, id):
    """ Not used......
    """
    PropertiesForm = form_for_model(Workflow, fields=('name','public','description','valid_users'), formfield_callback=formfield_callback)
    if request.user.is_staff:
        form = PropertiesForm(workflow)

def parameters(request, actor_path):
    """ If a GET request, generate a form for the requested actors
    properties and return a page displaying that form. If a POST
    request, save the parameters passed via the POST variable.
    """
    path = actor_path.split('/')
    w_id = path[0]
    model, workflow = open_workflow(request.user, w_id)
    # check permissions
    if not workflow.public and workflow.owner != request.user and request.user not in workflow.valid_users.all():
        raise Http404
    properties = model.get_properties(path[1:])
    ActorForm = generate_parameters_form(workflow, model, path[1:])
    url = reverse('parameters', args=(actor_path,))
    if request.POST:
        try:
            form = ActorForm(request.POST)
            save_parameters_from_post(workflow, request.POST, request.FILES)
        except:
            traceback.print_exc()
    else:
        form = ActorForm()
        pass
    actor = {'name':path[-1], 'properties':properties, 'path':actor_path}
    return render_to_response('kepler/parameters.html', {'form': form, 'url': url, 'actor': actor}, context_instance=RequestContext(request))

def delete_workflow(request, id):
    """ Handles deleting a workflow. If a GET request then display a
    page asking for conformation of the delete. If a POST request then
    set the workflow to deleted.
    """
    user = User.objects.get(id=request.user.id)
    workflow = Workflow.objects.get(pk=id)
    if workflow.owner != user:
        # the message here doesn't actually get passed. TODO: fix it
        #raise PermissionDenied('''you don't have permission to delete this workflow: you are not the owner''')
        request.user.message_set.create(message={'type':'ERROR', 'message':'You don\'t have permission to delete this workflow'})
        return HttpResponseRedirect(reverse('workflow_view', args=id))
    if request.POST:
        workflow.deleted = True
        workflow.save()
        msg = 'The workflow "%s" was deleted successfully' % workflow.name
        request.user.message_set.create(message=msg)
        return HttpResponseRedirect(reverse('workflows'))
    return render_to_response('kepler/delete_confirmation.html', {'workflow': workflow}, context_instance=RequestContext(request))
delete_workflow = login_required(delete_workflow)

def job_details(request, job_id):
    """ Handles displaying the details of a Job, including the
    properties form for specifying Job metadata (i.e. name and
    description).
    """
    job = get_object_or_404(Job, pk=job_id)
    outputs = []
    PropertiesForm = form_for_instance(job, fields=('name','description'))
    if request.method == 'POST':
        form = PropertiesForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse('')
        else:
            return HttpResponseServerError('')

    for o in [j for j in job.get_job_outputs() if j.name != 'Provenance Data']:
        out = {'name': o.name, 'type': o.type }
        print out
        if o.type == 'XML':
            data = open(o.file, 'r').read()
            # highlight would be awesome, but it takes forever on jython
                #hl = highlight(data, XmlLexer(), HtmlFormatter())
            out['content'] = data
            out['type'] = 'TEXT'
        if o.type == 'TEXT':
            f = open(o.file, 'r')
            out['content'] = mark_safe('<pre>%s</pre>' % f.read())
        elif o.type == 'IMAGE' or o.type == 'FILE':
            out['url'] = reverse('serve_job_media', args=(job_id, o.pk))
        outputs.append(out)
    if job.status == 'ERROR':
        request.user.message_set.create(message={'type':'ERROR', 'message':'An error occured while running this job, see below for details'})
    return render_to_response('kepler/job.html', {'crumbs': [{'name': 'Jobs', 'path': reverse('jobs')},], 'form': mark_safe(PropertiesForm().as_table().replace('\n','')), 'title': _(job), 'job': job, 'outputs': outputs}, context_instance=RequestContext(request))
job_details = login_required(job_details)

def job_media(request, job_id, output_id):
    """ Serves media from specific job runs.
    """
    job = get_object_or_404(Job, pk=job_id)
    out = get_object_or_404(JobOutput, pk=output_id)
    # TODO: do check to make sure job_id == out.job.pk
    # the [1:] is to remove the / from the start of the filename
    return serve(request, out.file[1:], '/')
job_media = login_required(job_media)

def workflows(request):
    """ Handles displaying the view of a searchable list of all the
    workflows on the system.
    """
    results = WorkflowList(request, 'workflow_view')
    c = RequestContext(request,
            { 'title': _('Workflows'),
              'results': results.result_list,
              'result_headers': results.result_headers,
              'query': results.query,
              'search_var': SEARCH_VAR,
              'pagination_required': results.pagination_required,
              'pages': results.pages,
              'page_count': len(results.pages),
              'result_count': len(results.result_list),
              'show_result_count': len(results.result_list) != results.full_result_count and results.query != '',
              'full_result_count': results.full_result_count,
              'crumbs': [''],
            })
    return render_to_response('kepler/workflow_list.html', context_instance=c)

def jobs(request):
    """ Handles displaying the view of a searchable list of all the jobs
    on the system.
    """
    results = JobList(request, 'job_details_view')
    c = RequestContext(request,
            { 'title': _('Jobs'),
              'results': results.result_list,
              'result_headers': results.result_headers,
              'query': results.query,
              'search_var': SEARCH_VAR,
              'pagination_required': results.pagination_required,
              'pages': results.pages,
              'page_count': len(results.pages),
              'result_count': len(results.result_list),
              'show_result_count': len(results.result_list) != results.full_result_count and results.query != '',
              'full_result_count': results.full_result_count,
              'crumbs': [''],
            })
    return render_to_response('kepler/workflow_list.html', context_instance=c)
jobs = login_required(jobs)

def duplicate_workflow(request, id):
    """ Takes a Workflow and makes an exact copy of it which can be
    modified seperatly from the original.
    """
    user = User.objects.get(id=request.user.id)
    workflow = get_object_or_404(Workflow, pk=id)
    if not workflow.public and workflow.owner != request.user and request.user not in workflow.valid_users.all():
        raise Http404
    workflow_copy = Workflow()
    i = 1
    name = '%s (copy)' % workflow.name
    while len(Workflow.objects.filter(name=name)) > 0:
        name = '%s (copy %d)' % (workflow.name, i)
        i += 1
    workflow_copy.name = name
    workflow_copy.owner = user
    workflow_copy.public = False
    workflow_copy.description = workflow.description
    filename = workflow.moml_file
    while os.path.exists('%s/%s' % (MEDIA_ROOT, filename)):
        filename = '%s%d%s' % (workflow.moml_file[:workflow.moml_file.rindex('.')], i, workflow.moml_file[workflow.moml_file.rindex('.'):])
        i += 1
    shutil.copyfile('%s/%s' % (MEDIA_ROOT, workflow.moml_file), '%s/%s' % (MEDIA_ROOT, filename))
    workflow_copy.moml_file = filename
    workflow_copy.save()
    for p in workflow.get_all_parameters():
        p_copy = WorkflowParameter()
        p_copy.workflow = workflow_copy
        p_copy.property_id = p.property_id
        p_copy.expose_to_user = p.expose_to_user
        p_copy.description = p.description
        p_copy.name = p.name
        p_copy.value = p.value
        p_copy.type = p.type
        p_copy.save()
    request.user.message_set.create(message={'type':'MESSAGE', 'message':'workflow has been successfully duplicated'})
    return HttpResponseRedirect(reverse('workflow_view', args=(workflow_copy.pk,)))

def download_workflow(request, id):
    """ Serves the Workflow MoML file.
    """
    user = User.objects.get(id=request.user.id)
    workflow = get_object_or_404(Workflow, pk=id)
    if not workflow.public and workflow.owner != request.user and request.user not in workflow.valid_users.all():
        raise Http404
    return serve(request, workflow.moml_file, MEDIA_ROOT)
