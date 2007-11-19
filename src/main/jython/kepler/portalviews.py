import time, md5, traceback, copy, array

from django import oldforms #, template
from django.template.context import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.datastructures import FileDict
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist, PermissionDenied
from django.views.static import serve

from workflow.proxy import ModelProxy
from workflow.utils import validateMoML
from workflow.cache import open_workflow, open_workflow_from_object, delete_workflow as dwf
from workspaces import *
from portalviewshelper import *
from models import *
from job import *
from settings import STORAGE_ROOT
from django.newforms import form_for_model

def welcome(request):
    return render_to_response('kepler/base_site.html', {'title': _('Welcome')}, context_instance=RequestContext(request))

def dashboard(request):
    workflows = [i for i in Workflow.objects.filter(public=True)]
    jobs = []
    if request.user.is_authenticated():
        workflows.extend([i for i in Workflow.objects.filter(owner=request.user) if i not in workflows])
        jobs = Job.objects.filter(owner=request.user).order_by('-submission_date')
        if len(jobs) > 5:
            jobs = jobs[:5]
    else:
        # set the test cookie, so that if the user decides to log in the login form actually works
        request.session.set_test_cookie()

    return render_to_response('kepler/dashboard.html', {'next': reverse('dashboard'), 'title': _('Dashboard'), 'workflows': workflows, 'jobs': jobs}, context_instance=RequestContext(request))
dashboard = login_required(dashboard)

def upload_workflow(request):
    WorkflowForm = form_for_model(Workflow)
    if request.method == 'POST':
        form = WorkflowForm(request.POST, request.FILES)
        if form.is_valid():
            messages = []
            workflow = form.save(commit=False)
            workflow.owner = request.user
            workflow.save()
            messages.append({'type':'MESSAGE', 'message':'The workflow "%s" was uploaded successfully' % workflow.name})
            for msg in messages:
                request.user.message_set.create(message=msg['message'])
            return HttpResponseRedirect(reverse('dashboard'))
    else:
        form = WorkflowForm()
    return render_to_response('kepler/upload_workflow.html', {'title': _('Upload Workflow'), 'crumbs': [''], 'form': form.as_table() }, context_instance=RequestContext(request))
upload_workflow = login_required(upload_workflow)

def workflow(request, id, edit_mode=False):
    workflow = get_object_or_404(Workflow, pk=id)
    if request.method == 'POST':
        print request.POST
        job = Job(workflow=workflow, owner=request.user, status='NEW')
        job.save()
        setup_job_parameters_from_post(job, request.POST)
        queue_new_job(job)
        return HttpResponseRedirect(reverse('job_details_view', args=(job.pk,)))
    return render_to_response('kepler/view_workflow.html', {'crumbs': [{'name': 'Workflows', 'path': reverse('workflows')},], 'editable': edit_mode, 'next': reverse('workflow_view', args=(id,)), 'title': _(workflow.name), 'workflow': workflow, }, context_instance=RequestContext(request))

def model(request, path):
    p = path.split('/')
    w_id = p[0]
    model, workflow = open_workflow(request.user, w_id)
    crumbs = build_crumbs_from_path(workflow.name, path)
    if len(p) > 1:
        name = p[-1]
    else:
        name = workflow.name
    props = reverse('properties', args=(path,))
    return render_to_response('kepler/workflow_canvas.html', {'crumbs': crumbs, 'editable': request.GET.get('editable', False), 'next': reverse('model_view', args=(path,)), 'title': _(name), 'workflow': workflow, 'model': model.get_as_dict(p[1:]), 'properties_url_base': props}, context_instance=RequestContext(request))

def job_form(request, id):
    workflow = get_object_or_404(Workflow, pk=id)
    JobSubmissionForm = generate_job_submission_form(workflow)
    if JobSubmissionForm is not None:
        params = JobSubmissionForm()
    else:
        params = None
    return render_to_response('kepler/parameters_form.html', { 'workflow': workflow, 'parameters': params }, context_instance=RequestContext(request))

def properties(request, actor_path):
    path = actor_path.split('/')
    w_id = path[0]
    if '__loading__' in path:
        return render_to_response('kepler/properties.html', {'loading':True}, context_instance=RequestContext(request))
    if '__none__' in path:
        return HttpResponse('')
    model, workflow = open_workflow(request.user, w_id)
    properties = model.get_properties(path[1:])
    ActorForm = generate_parameters_form(workflow, model, path[1:])
    url = reverse('properties', args=(actor_path,))
    if request.POST:
        try:
            form = ActorForm(request.POST)
            save_parameters_from_post(workflow, request.POST)
        except:
            traceback.print_exc()
    else:
        form = ActorForm()
        pass
    actor = {'name':path[-1], 'properties':properties, 'path':actor_path}
    return render_to_response('kepler/properties.html', {'form': form, 'url': url, 'actor': actor}, context_instance=RequestContext(request))

def delete_workflow(request, id):
    user = User.objects.get(id=request.user.id)
    wm = Workflow.objects.get(pk=id)
    if wm.owner != user:
        # the message here doesn't actually get passed. TODO: fix it
        raise PermissionDenied('''you don't have permission to delete this workflow: you are not the owner''')
    if request.POST:
        dwf(user, workflow_id)
        msg = 'The workflow "%s" was deleted successfully' % wm.name
        request.user.message_set.create(message=msg)
        return HttpResponseRedirect(reverse('index_view'))
    workflow = { 'name': wm.name }
    crumbs = build_crumbs_from_path(wm.name, '%s/delete' % (path))
    return render_to_response('kepler/delete_confirmation.html', {'crumbs':crumbs, 'workflow': workflow}, context_instance=RequestContext(request))
delete_workflow = login_required(delete_workflow)

def job_details(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    outputs = []
    if job.status == 'DONE':
        for o in job.get_job_outputs():
            out = {'name': o.name, 'type': o.type }
            if o.type == 'TEXT':
                f = open(o.file, 'r')
                out['content'] = f.read()
            elif o.type == 'IMAGE':
                out['url'] = reverse('serve_job_media', args=(job_id, o.pk))
            outputs.append(out)
    return render_to_response('kepler/job.html', {'crumbs': [{'name': 'Jobs', 'path': reverse('jobs')},], 'title': _(job), 'job': job, 'outputs': outputs}, context_instance=RequestContext(request))
job_details = login_required(job_details)

def job_media(request, job_id, output_id):
    job = get_object_or_404(Job, pk=job_id)
    out = get_object_or_404(JobOutput, pk=output_id)
    # TODO: do check to make sure job_id == out.job.pk
    # the [1:] is to remove the / from the start of the filename
    return serve(request, out.file[1:], '/')
job_media = login_required(job_media)

def workflows(request):
    results = SearchList(request, Workflow, 'workflow_view')
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
    results = SearchList(request, Job, 'job_details_view')
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
