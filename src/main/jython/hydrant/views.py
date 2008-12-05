import time, md5, traceback, copy, array, shutil, random

from django import oldforms
from django.template.context import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from django.http import Http404, HttpResponseServerError, HttpResponse, HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage
from django.db import models
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist, PermissionDenied
from django.views.static import serve

#from pygments import highlight
#from pygments.lexers import XmlLexer
#from pygments.formatters import HtmlFormatter

#from kepler.workflow.utils import validateMoML
from kepler.workflow.cache import open_workflow, open_workflow_from_object
from portalviewshelper import *
from models import *
from forms import *
from job import *
from utils import *
from templatetags.textutils import timeuntil_with_secs
from settings import STORAGE_ROOT, MEDIA_ROOT
from django.forms import widgets
from django.utils.safestring import mark_safe, mark_for_escaping

def intro(request):
    return render_to_response('index.html', {}, context_instance=RequestContext(request))

def hide_workflows(request, path):
    """ Used to hide the path to the workflow xml files from everyone
    """
    raise Http404

def home(request):
    """ Displays the users dashboard. Includes lists of the last five
    uploaded Workflows and Jobs.
    """
    workflows = []
    jobs = []
    if request.user.is_authenticated():
        workflows.extend([i for i in Workflow.objects.filter(owner=request.user,deleted=False) if i not in workflows])
        jobs = Job.objects.filter(owner=request.user).order_by('-last_modified')
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

    jobform = JobPreviewForm(instance=workflow)

    spath = path.split('/')
    po = workflow.get_proxy_object()
    name = workflow.name

    # since we may be looking at a composite actor of the workflow
    # we have to do a bit of work to make sure we have the correct
    # proxy object.
    i = 0
    newspath = []
    while i < len(spath):
        if spath[i] != '': # this makes any number of '/'s that have been placed next to each other as part of the path only count as one.
            oldpo = po
            po = oldpo.get(spath[i])
            j = i
            i = i + 1
            # this solves the case where an actor name has a '/' in it.
            # basically it checks to see if a proxy object was found on the previous get(),
            # and if one was not found, add the '/' and the next section of the path and attempt
            # the get() again. This continues until a proxy object is found of the number of
            # path segments is exceeded.
            # TODO: if the actor name starts or ends with a '/' this will still fail
            while po == None and i < len(spath):
                i = i + 1
                po = oldpo.get('/'.join(spath[j:i]))

            if po == None:
                # if no proxy object was found, return a 404 error
                raise Http404
            else:
                # appends the actor name to a new path list.
                newspath.append('/'.join(spath[j:i]))
                name = po.name
        else:
            i = i + 1
    spath = newspath

    # build breadcrumbs so that when inside composite actors it is easy to go back.
    crumbs = []
    if len(spath) > 0 and spath[0] != '':
        crumbs.append({'name': workflow.name, 'url': reverse('workflow', args=(id,))})
        for i in range(len(spath[:-1])):
            crumbs.append({'name': spath[i], 'url': '%s%s/' % (reverse('workflow', args=(id,)), '/'.join(spath[:(i+1)])) })

    print crumbs

    stuff = {'crumbs': crumbs,
             'name': name,
             'editable': editable,
             'workflow': workflow,
             #'properties_form': pform is None and '' or pform
             }

    if request.method == 'POST' and request.POST.has_key('details'):
        ef = EditWorkflowForm(request.POST, instance=workflow)
        ef.save()
        
        for u in workflow.all_permitted_users():
            v_rmed = v_added = e_rmed = e_added = False
            has_edit = request.POST.get(u.username + '_edit', False)
            has_view = request.POST.get(u.username + '_view', has_edit)
            if not has_edit and workflow.has_edit_permission(u):
                workflow.edit_permissions.remove(u)
                e_rmed = True
            if has_edit and not workflow.has_edit_permission(u):
                workflow.edit_permissions.add(u)
                e_added = True
            if not has_view and workflow.has_view_permission(u):
                workflow.view_permissions.remove(u)
                v_rmed = True
            if has_view and not workflow.has_view_permission(u):
                workflow.view_permissions.add(u)
                v_added = True
            msg_text = None
            if e_rmed or v_rmed:
                msg_text = '{{ touser }} can no longer %s this workflow' % (
                    e_rmed and v_rmed and 'view or edit' or e_rmed and 'edit' or 'view'
                    )
            if e_added or v_added:
                msg_text = '{{ touser }} can now %s this workflow' % (
                    e_added and v_added and 'view and edit' or e_added and 'edit' or 'view'
                    )
            if msg_text:
                msg = Message(touser=u,
                              fromuser=request.user,
                              # plural is the wrong term, should be something like ownership
                              verb='changed {{ touser|plural }} permissions for',
                              text=msg_text)
                msg.save()
                WorkflowMessage(workflow=workflow, message=msg).save()
        try:
            u = User.objects.get(username=request.POST['username'])
            has_edit = request.POST.get('has_edit', False)
            has_view = request.POST.get('has_view', has_edit)
            if has_view:
                workflow.view_permissions.add(u)
            if has_edit:
                workflow.edit_permissions.add(u)
            if has_edit or has_view:
                workflow.save()

            msg_text = '{{ touser }} can now %s this workflow' % (
                    has_view and has_edit and 'view and edit ' or has_edit and 'edit ' or 'view '
                    )
            msg = Message(touser=u,
                          fromuser=request.user,
                          verb='gave {{ touser }} permissions to',
                          text=msg_text)
            msg.save()
            WorkflowMessage(workflow=workflow, message=msg).save()
        except:
            pass        
    elif editable:
        ef = EditWorkflowForm(instance=workflow)

    if editable:
        stuff['editform'] = ef
        stuff['adduserform'] = AddUserForm()
    
    if jobform is not None:
        stuff['jobform'] = jobform

    if request.method == 'POST' and request.POST.has_key('reporterror'):
        message = request.POST.get('message')
        reported = False
        try:
            submit_ticket(workflow, request.user, message)
            reported = True
        except:
            traceback.print_exc()
            superuser = User.objects.filter(is_superuser=True)[0]
            msg = Message(touser=superuser,
                          fromuser=get_system_user(),
                          verb='reporting an error',
                          text='Problem with workflow id=%s. reported by %s with message: %s' % (
                workflow.pk,
                request.user,
                message,
                ))
            msg.save()
            UserMessage(subject='problem with workflow id=%s' % workflow.pk,
                        message=msg).save()
            reported = True
        if reported:
            stuff['reported'] = True    

    if po is None and workflow.error:
        stuff['workflowerror'] = workflow.error
        stuff['reporterrorform'] = CommentForm()
    else:
        if po.is_actor():
            if not editable:
                return HttpResponseRedirect('%s%s' % (reverse('workflow', args=(id,)), '/'.join(spath[:-1])))
            ActorForm = generate_parameters_form(workflow, po, [])
            if request.method == 'POST' and request.POST.has_key('parameters'):
                try:
                    save_parameters_from_post(workflow, request.POST, request.FILES)
                except:
                    traceback.print_exc();
                try:
                    return HttpResponseRedirect('%s%s' % (reverse('workflow', args=(id,)), '/'.join(spath[:-1])))
                except:
                    return HttpResponseRedirect(reverse('workflow', args=(id,)))
            stuff['form'] = ActorForm()
        else:
            stuff['model'] = po.get_as_dict()

    return render_to_response('view_workflow.html',
                              stuff,
                              context_instance=RequestContext(request))
workflow = login_required(workflow)

def delete_workflow(request, id, undelete=False):
    """ Handles deleting a workflow. If a GET request then display a
    page asking for conformation of the delete. If a POST request then
    set the workflow to deleted.
    """
    workflow = get_object_or_404(Workflow, pk=id)
    if not workflow.has_delete_permission(request.user):
        raise Http404

    if undelete == True:
        workflow.deleted = False
        workflow.save()

        if workflow.public == 'ON':
            tousers = [get_system_user()]
        else:
            tousers = [u for u in workflow.view_permissions.all()]
            tousers.append(workflow.owner)

        for u in tousers:
            msg = Message(touser=u,
                          fromuser=get_system_user(),
                          verb='undeleted',
                          text='This workflow can now be accessed again',
                          private = u != get_system_user()
                          )
            msg.save()
            WorkflowMessage(workflow=workflow, message=msg).save()
        
        return HttpResponseRedirect(reverse('workflow', args=(workflow.pk,)))

    if request.method == 'POST':
        if request.POST.has_key("YES"):
            workflow.deleted = True
            workflow.save()

            if workflow.public == 'ON':
                tousers = [get_system_user()]
            else:
                tousers = [u for u in workflow.view_permissions.all()]

            for u in tousers:
                msg = Message(touser=u,
                              fromuser=request.user,
                              verb='deleted',
                              text="""This workflow can no longer be accessed""",
                              private = u != get_system_user()
                              )
                msg.save()
                WorkflowMessage(workflow=workflow, message=msg).save()

        return HttpResponseRedirect(reverse('home'))
    return render_to_response('delete_workflow.html',
                              {'workflow': workflow},
                              context_instance=RequestContext(request)
                              )
delete_workflow = login_required(delete_workflow)

def job_create(request, workflowid):
    """ Creates a job from the workflow, and redirects the
    user to the job submission page for the newly created
    job.
    """
    wf=get_object_or_404(Workflow, pk=workflowid)
    if not wf.has_view_permission(request.user):
        raise Http404
    job = Job()
    job.workflow = wf
    job.name = wf.name + ' Job'
    job.owner = request.user
    job.save()
    return HttpResponseRedirect(reverse('job', args=(job.pk,)))
job_create = login_required(job_create)

def job_rerun(request, jobid):
    """ Creates a job based on another job. This copies all
    the inputs from the original job as well.
    """
    origjob=get_object_or_404(Job, pk=jobid)
    if not origjob.has_view_permission(request.user) or not origjob.workflow.has_view_permission(request.user):
        raise Http404
    job = Job(
        workflow=origjob.workflow,
        description=origjob.description,
        name=origjob.name + ' Re-run',
        owner=request.user,
        )
    job.save()
    for origji in origjob.get_job_inputs():
        ji = JobInput(job=job, parameter=origji.parameter, value=origji.value)
        ji.save()
    return HttpResponseRedirect(reverse('job', args=(job.pk,)))
job_create = login_required(job_create)

def job_stop(request, jobid):
    """ Either stops, or destroys a job based on the status of the job.
    """
    job = get_object_or_404(Job, pk=jobid)
    if job.status == 'QUEUED':
        # if the job is queued, call stop_job which will remove
        # the job from the queue.
        stop_job(job)
    if job.status == 'NEW' or job.status == 'QUEUED':
        # if the job is still NEW or QUEUED, destroy it, which involves
        # removing all the related job inputs.
        for i in job.get_job_inputs():
            i.delete()
        for o in job.get_job_outputs():
            o.delete()
        job.delete()
        # since the job no longer exists, redirect the user to their dashboard
        return HttpResponseRedirect(reverse('home',))
    else:
        # if the job is running, then stop the job. A job which has started
        # running or has finished running cannot be destroyed.
        stop_job(job)
        return HttpResponseRedirect(reverse('job', args=(job.pk,)))

def job(request, jobid):
    """ Handles displaying the details of a Job, including the
    properties form for specifying Job metadata (i.e. name and
    description).
    """
    job = get_object_or_404(Job, pk=jobid)

    # make sure the user who is requesting this job has permission
    # to look at is. If not, return a 404 error.
    if not job.has_view_permission(request.user):
        raise Http404
    
    outputs = []

    # grab the runtime inputs attached to the job.
    userinputs = []
    if job.status == 'WAITINGFORINPUT':
        userinputs = JobRuntimeInput.objects.filter(job=job,value=None)

    # if the key save_permissions is in the POST request this means that
    # the permissions form on the job page has been submitted.
    if request.method == 'POST' and request.POST.has_key('save_permissions'):
        # traverse through all the users who have view permissions, and check if
        # a key with their username + _remove is in the POST request and if so
        # remove the user from the view permissions.
        for u in job.view_permissions.all():
            if request.POST.get(u.username + '_remove', False):
                job.view_permissions.remove(u)
        try:
            # set if the job is public or not based on the POST key 'public'
            job.public = request.POST.get('public')

            # try to get the user specified in the POST key username.
            # if the user doesn't exist, this will throw a DoesNotExist exception
            # and will skip the rest of the block.
            u = User.objects.get(username=request.POST['username'])

            # if the user was found, add him/her to the view permissions
            job.view_permissions.add(u)

            # create a new job message about the changes to the job permissions.
            msg_text = '{{ touser }} can now view this job'
            msg = Message(touser=u,
                          fromuser=request.user,
                          verb='gave {{ touser }} permissions to',
                          text=msg_text)
            msg.save()
            JobMessage(job=job, message=msg).save()
        except:
            traceback.print_exc()
        # save the job.
        job.save()
    elif request.method == 'POST':
        # this case is tested if the POST wasn't for permission changes.
        # it handles the case where the workflow is waiting for user input and processes
        # the input form. If this is a job submit post, userinputs will be empty and no
        # processing will be done.
        for i in userinputs:
            # each runtime input submission is defined by the name of the actor which
            # requested the input. Thus, if this is a POST to submit a value for a runtime
            # input, there will be be a key in the POST request which matches one of the
            # runtime inputs that still needs to be specified.
            if request.POST.has_key(i.actor):
                i.value = request.POST.get('inputvalue')
                i.save()
                # remove this input from the query
                userinputs = userinputs.exclude(pk=i.pk)
                # now that one of the inputs have been set, check to see if there
                # are anymore
                if len(userinputs) < 1:
                    job.status = 'RUNNING'
                    job.save()
                # next grab the thread which is running the job
                t = execution.default_job_manager.get_thread_for_job(job)
                # and tell it that a value for it's runtime input has been set.
                t.replacement_manager.sendResultToWaitingInput(i)
                # send a redirect back to this page. This removes the POST request
                # from the page making it possible to hit the refresh button in the
                # browser without being harrassed about sending the POST again.
                return HttpResponseRedirect(reverse('job', args=(job.pk,)))

    # 'stuff' is the context dictionary that gets send to the page template.
    stuff = {'job': job,}

    # if the user requesting the page is the same user whom owns the job
    # add the job permissions form to 'stuff'
    if request.user == job.owner:
        stuff['permissionsform'] = JobPermissionsForm(instance=job)

    if job.status == 'NEW' and request.user == job.owner:
        # if a POST request has been made, the job has not yet been started and the
        # save_permissions key isn't in the request than this POST is a job submission
        # request.
        if request.method == 'POST' and not request.POST.has_key('save_permissions'):
            # get the job creation form with the request variables loaded into it.
            jobform = JobCreationForm(request.POST, request.FILES, instance=job)
            if jobform.is_valid():
                if request.POST.has_key('save_job'):
                    jobform.save() # need a save for later type thing
                elif request.POST.has_key('run_job'):
                    jobform.save()
                    # create a message to say the job has been submitted
                    msg = Message(touser=get_system_user(),
                                  fromuser=request.user,
                                  verb='submitted',
                                  text=job.description)
                    msg.save()
                    JobMessage(job=job, message=msg).save()
                    # queue the new job
                    queue_new_job(job)
                return HttpResponseRedirect(reverse('job', args=(job.pk,)))
            else:
                print jobform.errors
        else:
            # if we don't have a POST request, generate the standard job creation form
            jobform = JobCreationForm(instance=job)
        # add the job form to 'stuff'
        stuff['jobform'] = jobform

    if job.status == 'WAITINGFORINPUT' and request.user == job.owner:
        stuff['inputs'] = userinputs

    for o in [j for j in job.get_job_outputs() if j.name != 'Provenance Data']:
        out = {'name': o.name, 'type': o.type }
        if o.type == 'ERROR':
            o.type = out['type'] = 'TEXT'
            out['error'] = True
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
        print out
        outputs.append(out)

    # if there are outputs to be displayed, add them to 'stuff'
    if len(outputs):
        stuff['outputs'] = outputs

    # render the job template
    return render_to_response('job.html',
                              stuff,
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
        results = Workflow.objects.all().order_by('-created')
        prefix = '?'
    permission_based_results = []
    for w in results:
        if request.user.is_superuser or not w.deleted:
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
        results = Job.objects.all().order_by('-creation_date')
        prefix = '?'
    permission_based_results = []
    for j in results:
        if j.has_view_permission(request.user):
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
    workflow_copy.owner = request.user
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
    return HttpResponseRedirect(reverse('workflow', args=(workflow_copy.pk,)))

def download_workflow(request, id):
    """ Serves the Workflow MoML file.
    """
    user = User.objects.get(id=request.user.id)
    workflow = get_object_or_404(Workflow, pk=id)
    if not workflow.public and workflow.owner != request.user and request.user not in workflow.valid_users.all():
        raise Http404
    return serve(request, workflow.moml_file, MEDIA_ROOT)
download_workflow = login_required(download_workflow)

def profile(request, username):
    user = get_object_or_404(User, username=username)
    stuff = {'requested_user': user,}
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST' and request.POST.has_key('profile'):
        infoform = UserInfoForm(request.POST, instance=profile)
        profile = infoform.save()
        stuff['profilesaved'] = True
    else:
        infoform = UserInfoForm(instance=profile)

    if request.method == 'POST' and request.POST.has_key('password'):
        pwcf = PasswordChangeForm(request.user, request.POST)
        if pwcf.is_valid():
            pwcf.save()
            stuff['passwordsaved'] = True
            pwcf = PasswordChangeForm(request.user)
    else:
        pwcf = PasswordChangeForm(request.user)

    if request.method == 'POST' and request.POST.has_key('sendmessage'):
        cf = CommentForm(request.POST)
        if cf.is_valid():
            msg = Message(touser=user,
                          fromuser=request.user,
                          verb='sent {{ touser }} a message',
                          text=cf.cleaned_data['message'])
            msg.save()
            UserMessage(subject=cf.cleaned_data['subject'], message=msg).save()
            stuff['sent'] = True
            cf = CommentForm()
        else:
            print cf.errors
    else:
        cf = CommentForm()

    if user == request.user:
        stuff['infoform'] = infoform
        stuff['passwordform'] = pwcf
    else:
        stuff['profile'] = profile
        stuff['messageform'] = cf

        
    return render_to_response('profile.html',
                              stuff,
                              context_instance=RequestContext(request))
profile = login_required(profile)

def signup(request):
    stuff = {}
    if request.method == 'POST':
        signupform = SignupForm(request.POST)
        if signupform.is_valid():
            u,p = signupform.save()
            stuff['signupsuccessful'] = True
        else:
            stuff['signupform'] = signupform
    else:
        signupform = SignupForm()
        stuff['signupform'] = signupform
    return render_to_response('signup.html',
                              stuff,
                              context_instance=RequestContext(request))
