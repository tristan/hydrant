import time, md5, traceback, copy, array, shutil, random

from django import oldforms #, template
from django.template.context import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from django.http import Http404, HttpResponseServerError, HttpResponse, HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage
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
from forms import *
from job import *
from templatetags.textutils import timeuntil_with_secs
from settings import STORAGE_ROOT, MEDIA_ROOT
from django.newforms import form_for_model, form_for_instance, widgets
from django.utils.safestring import mark_safe, mark_for_escaping

def intro(request):
    return render_to_response('kepler/intro.html', {'pic_no':random.randint(0,10)}, context_instance=RequestContext(request))

def hide_workflows(request, path):
    """ Used to hide the path to the workflow xml files from everyone
    """
    raise Http404

def home(request):
    """ Displays the users dashboard. Includes lists of the last five
    uploaded Workflows and Jobs.
    """
    workflows = [i for i in Workflow.objects.filter(public=True,deleted=False)]
    jobs = []
    if request.user.is_authenticated():
        workflows.extend([i for i in Workflow.objects.filter(owner=request.user,deleted=False) if i not in workflows])
        jobs = Job.objects.filter(owner=request.user)
        if len(jobs) > 5:
            jobs = jobs[:5]
        messages = get_all_messages_related_to_user(request.user).order_by('-date')
        messages = messages[:10] #limit to the last ten messages
        return render_to_response('dashboard.html',
                                  {'next': reverse('dashboard'),
                                   'title': _('Dashboard'),
                                   'workflows': workflows,
                                   'jobs': jobs,
                                   'messages': messages
                                   },
                                  context_instance=RequestContext(request))
    else:
        # set the test cookie, so that if the user decides to log in the login form actually works
        request.session.set_test_cookie()
        return render_to_response('index.html', context_instance=RequestContext(request))

def upload_workflow(request):
    """ Handles uploading a Workflow. If a GET request is made, then
    return a page displaying the upload form. If a POST request is made,
    check the POST and FILES variables for Workflow details and store
    them.
    """
    if request.method == 'POST':
        print request.POST
        form = UploadWorkflowForm(request.POST, request.FILES)

        if form.is_valid() and form.validate_moml():
            messages = []
            workflow = form.save(commit=False)
            workflow.owner = request.user
            workflow.save()
            form.save_m2m()

            msg = Message(touser=get_system_user(),
                          fromuser=request.user,
                          verb='uploaded',
                          text=workflow.description,
                          private=workflow.public == 'OFF'
                          )
            msg.save()
            WorkflowMessage(workflow=workflow, message=msg).save()
            
            return HttpResponseRedirect(reverse('workflow', args=(workflow.pk,)))
            
        else:
            print form.errors
    else:
        form = UploadWorkflowForm()
    return render_to_response('upload_workflow.html',
                              {'title': _('Upload Workflow'),
                               'crumbs': [''],
                               'form': form
                               },
                              context_instance=RequestContext(request))
upload_workflow = login_required(upload_workflow)

def workflow(request, id, path=''):
    """ If a GET request, returns the page which displays a Workflow. If
    a POST request, checks the POST variables for Workflow metadata
    values and stores them for the specified workflow.
    """
    workflow = get_object_or_404(Workflow, pk=id)
    # check permissions
    if not workflow.has_view_permission(request.user):
        raise Http404

    editable = workflow.has_edit_permission(request.user)

    jobform = None
    JobSubmissionForm = generate_job_submission_form(workflow)
    if JobSubmissionForm is not None:
        jobform = JobSubmissionForm()

    spath = path.split('/')
    po = workflow.get_proxy_object()
    name = workflow.name
    for i in spath:
        if i != '':
            po = po.get(i)
            name = po.name
    crumbs = []
    if len(spath) > 0 and spath[0] != '':
        crumbs.append({'name': workflow.name, 'url': reverse('workflow', args=(id,))})
        for i in range(len(spath[:-1])):
            crumbs.append({'name': spath[i], 'url': reverse('workflow', args=(id,'/'.join(spath[:i])))})
    stuff = {'crumbs': crumbs,
             'name': name,
             'editable': editable,
             'workflow': workflow,
             #'properties_form': pform is None and '' or pform
             }
    if jobform is not None:
        stuff['jobform'] = jobform
    if po.is_actor():
        ActorForm = generate_parameters_form(workflow, po, [])
        if request.POST:
            try:
                #form = ActorForm(request.POST)
                save_parameters_from_post(workflow, request.POST, request.FILES)
            except:
                traceback.print_exc();
            return HttpResponseRedirect(reverse('workflow', args=(id,'/'.join(spath[:-1]))))
            
        stuff['form'] = ActorForm()
    else:
        stuff['model'] = po.get_as_dict()

    return render_to_response('view_workflow.html',
                              stuff,
                              context_instance=RequestContext(request))

def edit_workflow(request, id):
    w = get_object_or_404(Workflow, pk=id)
    if not w.has_edit_permission(request.user):
        raise Http404

    if request.method == 'POST':

        ef = EditWorkflowForm(request.POST, instance=w)
        ef.save()
        
        for u in w.all_permitted_users():
            v_rmed = v_added = e_rmed = e_added = False
            has_edit = request.POST.get(u.username + '_edit', False)
            has_view = request.POST.get(u.username + '_view', has_edit)
            if not has_edit and w.has_edit_permission(u):
                w.edit_permissions.remove(u)
                e_rmed = True
            elif has_edit and not w.has_edit_permission(u):
                w.edit_permissions.add(u)
                e_added = True
            if not has_view and w.has_view_permission(u):
                w.view_permissions.remove(u)
                v_rmed = True
            elif has_view and not w.has_view_permission(u):
                w.view_permissions.add(u)
                v_added = True
            msg_text = None
            if e_rmed or v_rmed:
                msg_text = '{{ touser }} can no longer %s this workflow' % (
                    e_rmed and v_rmed and 'view or edit ' or e_rmed and 'edit ' or 'view '
                    )
            if e_added or v_added:
                msg_text = '{{ touser }} can now %s this workflow' % (
                    e_added and v_added and 'view and edit ' or e_added and 'edit ' or 'view '
                    )
            if msg_text:
                msg = Message(touser=u,
                              fromuser=request.user,
                              verb='changed {{ touser|plural }} permissions for',
                              text=msg_text)
                msg.save()
                WorkflowMessage(workflow=w, message=msg).save()
        try:
            u = User.objects.get(username=request.POST['username'])
            has_edit = request.POST.get('has_edit', False)
            has_view = request.POST.get('has_view', has_edit)
            if has_view:
                w.view_permissions.add(u)
            if has_edit:
                w.edit_permissions.add(u)
            if has_edit or has_view:
                w.save()

            msg_text = '{{ touser }} can now %s this workflow' % (
                    has_view and has_edit and 'view and edit ' or has_edit and 'edit ' or 'view '
                    )
            msg = Message(touser=u,
                          fromuser=request.user,
                          verb='gave {{ touser }} permissions to',
                          text=msg_text)
            msg.save()
            WorkflowMessage(workflow=w, message=msg).save()
        except:
            pass
    else:
        ef = EditWorkflowForm(instance=w)

    # just because permissions can change during POST processing
    if not w.has_edit_permission(request.user):
        raise Http404
           
    stuff = {'workflow': w,
             'adduserform': AddUserForm(),
             'editform': ef,
             }
    return render_to_response('view_workflow.html',
                              stuff,
                              context_instance=RequestContext(request))

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

def job_create(request, workflowid):
    workflow=get_object_or_404(Workflow, pk=workflowid)
    job = Job()
    job.workflow = workflow
    job.name = workflow.name + ' Job'
    job.owner = request.user
    job.save()
    return HttpResponseRedirect(reverse('job', args=(job.pk,)))

def job(request, jobid):
    """ Handles displaying the details of a Job, including the
    properties form for specifying Job metadata (i.e. name and
    description).
    """
    job = get_object_or_404(Job, pk=jobid)
    outputs = []
    if job.status == 'NEW':
        if request.method == 'POST':
            save_job_form(job, request.POST, request.FILES)
            if request.POST.has_key('save_job'):
                pass
            elif request.POST.has_key('run_job'):
                msg = Message(touser=get_system_user(),
                              fromuser=request.user,
                              verb='submitted',
                              text=job.description)
                msg.save()
                JobMessage(job=job, message=msg).save()
                queue_new_job(job)
                return HttpResponseRedirect(reverse('job', args=(job.pk,)))

        JobSubmissionForm = generate_job_submission_form(job.workflow, job)
        if JobSubmissionForm is not None:
            jobform = JobSubmissionForm()
        else:
            jobform = None
        return render_to_response('job.html',
                                  {'jobform': jobform,
                                   'job': job,
                                   },
                                  context_instance=RequestContext(request))

    for o in [j for j in job.get_job_outputs() if j.name != 'Provenance Data']:
        out = {'name': o.name, 'type': o.type }

        if o.type == 'URI':
            if o.file.lower().startswith('file://'):
                out['url'] = reverse('serve_job_media', args=(jobid, o.pk))
            else:
                out['url'] = o.file
        if o.type == 'XML':
            data = open(o.file, 'r').read()
            # highlight would be awesome, but it takes forever on jython
                #hl = highlight(data, XmlLexer(), HtmlFormatter())
            out['content'] = data
            out['type'] = 'TEXT'
        if o.type == 'TEXT':
            f = open(o.file, 'r')
            out['content'] = mark_for_escaping(f.read())
        elif o.type == 'IMAGE' or o.type == 'FILE':
            out['url'] = reverse('serve_job_media', args=(jobid, o.pk))
        outputs.append(out)
    return render_to_response('job.html',
                              {'job': job,
                               'outputs': outputs
                               },
                              context_instance=RequestContext(request))
job = login_required(job)

def job_media(request, job_id, output_id):
    """ Serves media from specific job runs.
    """
    job = get_object_or_404(Job, pk=job_id)
    out = get_object_or_404(JobOutput, pk=output_id)
    # TODO: do check to make sure job_id == out.job.pk
    # the [1:] is to remove the / from the start of the filename
    if out.file.lower().startswith('file://'):
        f = out.file[8:]
    else:
        f = out.file[1:]
    return serve(request, f, '/')
job_media = login_required(job_media)

def workflows(request):
    """ Handles displaying the view of a searchable list of all the
    workflows on the system.
    """
    if request.GET.has_key('search_term'):
        form = WorkflowSearchForm(request.GET)
        results = form.get_results()
        prefix = form.get_url()
    else:
        form = WorkflowSearchForm()
        results = Workflow.objects.all()
        prefix = '?'
    permission_based_results = []
    for w in results:
        if w.has_view_permission(request.user):
            if w.has_edit_permission(request.user):
                w.user_can_edit = True
            permission_based_results.append(w)
        
    results = permission_based_results
    paginator = Paginator(results, 8)
    try:
        page = paginator.page(int(request.GET.get('p', 1)))
    except:
        page = paginator.page(1)
    return render_to_response('list.html',
                              {'page':page,
                               'workflow': True,
                               'form': form,
                               'prefix': prefix,
                               },
                              context_instance=RequestContext(request))

def jobs(request):
    """ Handles displaying the view of a searchable list of all the jobs
    on the system.
    """
    if request.GET.has_key('search_term'):
        form = JobSearchForm(request.GET)
        results = form.get_results()
        prefix = form.get_url()
    else:
        form = JobSearchForm()
        results = Job.objects.all()
        prefix = '?'
    permission_based_results = []
    for j in results:
        if j.workflow.has_view_permission(request.user):
            permission_based_results.append(j)
    results = permission_based_results
    paginator = Paginator(results, 8)
    try:
        page = paginator.page(int(request.GET.get('p', 1)))
    except:
        page = paginator.page(1)
    return render_to_response('list.html',
                              {'page':page,
                               'job': True,
                               'form': form,
                               'prefix': prefix,
                               },
                              context_instance=RequestContext(request))
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
