import time, md5, traceback, copy

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

import repository
from workflow.proxy import ModelProxy
from workflow.cache import open_workflow, delete_workflow as dwf
from workspaces import *
from portalviewshelper import *
from models import *

def index(request):
    workflows = [i for i in Workflow.objects.filter(public=True)]
    templates = [i for i in Template.objects.filter(public=True)]
    if request.user.is_authenticated():
        workflows.extend([i for i in Workflow.objects.filter(owner=request.user) if i not in workflows])
        templates.extend([i for i in Template.objects.filter(owner=request.user) if i not in templates])
    else:
        # set the test cookie, so that if the user decides to log in the login form actually works
        request.session.set_test_cookie()
    wf_list = []
    for i in workflows:
        owner = User.objects.get(id=i.owner_id)
        if owner.first_name and owner.last_name:
            owner = '%s %s' % (owner.first_name, owner.last_name)
        else:
            owner = owner.username
        metadata = {
                'id': i.id,
                'name': i.name,
                'owner': owner,
                'public': i.public,
                'view_url': reverse('portal_workflow_view', urlconf=None, args=(i.id,), kwargs=None),
                }
        wf_list.append(metadata)

    t_list = []
    for i in templates:
        t = {'id': i.id, 'name': i.name}
        t_list.append(t)
    workspace_list = list_active_workspaces(request.user)
    return render_to_response('kepler/index.html', {'next': reverse('index_view'), 'title': _('Home'), 'workflow_list': wf_list, 'template_list': t_list, 'workspace_list': workspace_list}, context_instance=RequestContext(request))

def workflow(request, path, is_workspace=False):
    p = path.split('/')
    w_id = p[0]
    if is_workspace:
        model = get_model_from_workspace(request.user, w_id)
        actor = request.session.get('open_actor_properties')
        is_template = is_templating_workspace(request.user, w_id)
        if actor:
            del request.session['open_actor_properties']
    else:
        model, workflow = open_workflow(request.user.is_authenticated() and User.objects.get(id=request.user.id) or None, w_id)
        actor = None
        is_template = false
    results = model.get_as_dict(p[1:])
    crumbs = build_crumbs_from_path(model, path)
    return render_to_response('kepler/view_workflow.html', {'open_actor_properties': actor, 'is_workspace': is_workspace, 'crumbs': crumbs, 'next': reverse(is_workspace and 'portal_workspace_view' or 'portal_workflow_view', args=(path,)), 'title': '%s%s' % (_(model.name), is_workspace and ' Workspace' or ''), 'workflow': results, 'is_template': is_template}, context_instance=RequestContext(request))

def properties(request, actor_path, is_workspace=False):
    path = actor_path.split('/')
    w_id = path[0]
    if '__none__' in path:
        return render_to_response('kepler/properties.html', {'loading':True}, context_instance=RequestContext(request))
    if is_workspace:
        model = get_model_from_workspace(request.user, w_id)
        is_template = is_templating_workspace(request.user, w_id)
    else:
        model, workflow = open_workflow(request.user.is_authenticated() and User.objects.get(id=request.user.id) or None, w_id)
        is_template = False
    properties = model.get_properties(path[1:])
    if request.POST:
        if is_template:
            template = get_template_from_workspace(request.user, w_id)
            print request.POST
            #request.user.message_set.create(message='templating still not fully implemented')
            for p in properties:
                name = p['name']
                node_id = p['id']
                node = get_node_with_id(request.user, w_id, node_id)
                if request.POST.has_key('%s_enable_template' % name):
                    if not node:
                        # create new node
                        print 'creating new node with id: %s' % node_id
                        node = TemplateNode(template=template, property_id=node_id)
                        add_new_node(request.user, w_id, node_id, node)
                    # update node
                    for i in ['default_value', 'display_name', 'description']:
                        key = '%s_%s' % (name, i)
                        if request.POST.has_key(key):
                            value = request.POST.get(key)
                            print 'updating %s with %s' % (key, value)
                            setattr(node, i, value)
                else:
                    if node:
                        pass # delete node
                    else:
                        pass # ignore


        else:
            for i in request.POST:
                old = model.get_actor_property(path[1:], i)
                new = request.POST.get(i)
                if old != new:
                    model.set_actor_property(path[1:], i, request.POST[i])
                    request.user.message_set.create(message='updated value for %s' % i)
    if is_template:
        # change properties to templating model
        template = get_template_from_workspace(request.user, w_id)
        print properties
        np = []
        for p in properties:
            q = copy.copy(p)
            node_id = p['id']
            node = get_node_with_id(request.user, w_id, node_id)
            if not node:
                q['enabled'] = False
                q['description'] = ''
                q['display_name'] = p['name']
            else:
                q['enabled'] = True
                q['description'] = node.description
                q['display_name'] = node.display_name
                q['value'] = node.default_value
            np.append(q)
        properties = np
    else:
        properties = model.get_properties(path[1:])
    actor = {'name':path[-1], 'properties':properties, 'path':actor_path}
    return render_to_response('kepler/properties.html', {'is_workspace': is_workspace, 'is_template': is_template, 'actor': actor}, context_instance=RequestContext(request))

def start_workflow_edit(request, actor_path, template=False):
    path = actor_path.split('/')
    workflow_id = path[0]
    workspace_id = create_workspace(request.user, workflow_id, template)
    m = get_model_from_workspace(request.user, workspace_id)
    msg = 'New %s for workflow "%s" was created successfully' % (template and 'template' or 'workspace', m.name)
    request.user.message_set.create(message=msg)
    np = [workspace_id]
    if m.is_actor(path[1:]):
        request.session['open_actor_properties'] = path[-1]
        np.extend(path[1:-1])
    else:
        np.extend(path[1:])
    return HttpResponseRedirect(reverse('portal_workspace_view', args=('/'.join(np),)))
start_workflow_edit = login_required(start_workflow_edit)

def save_workspace(request, path):
    p = path.split('/')
    workspace_id = path[0]
    m = get_model_from_workspace(request.user, workspace_id)
    orig_workflow_id = get_original_workflow_id(request.user, workspace_id)
    is_template = is_templating_workspace(request.user, workspace_id)
    if request.POST:
        if is_template:
            print request.POST
            overwrite = request.POST.get('overwrite', 'off') == 'on'
            public = request.POST.get('public', 'off') == 'on'
            name = request.POST.get('name', m.name)
            save_templating_workspace(request.user, workspace_id, name, public, overwrite)
            msg = 'template %s saved successfully' % name
            request.user.message_set.create(message=msg)
        else:
            print request.POST
            workflow = request.POST.copy()
            name = workflow.get('name')
            if m.name != name:
                m.model.name = name
            d = time.localtime()
            mxml = m.get_xml()
            workflow['uri_file'] = FileDict({'content-type': 'text/xml', 'filename': md5.new('%s%s%s%s' % (request.user.username, m.name, mxml, d)).hexdigest(), 'content': mxml})
            if request.POST.get('overwrite'):
                update_existing_workflow(workflow, orig_workflow_id)
            else:
                workflow['owner'] = unicode(request.user.pk)
                workflow['created_date'] = unicode(time.strftime('%Y-%m-%d', d))
                workflow['created_time'] = unicode(time.strftime('%H:%M:%S', d))
                add_new_workflow(workflow)
            msg = 'The workflow "%s" was saved successfully' % workflow.get('name')
            request.user.message_set.create(message=msg)
        if request.POST.has_key('_continue'):
            return HttpResponseRedirect(reverse('portal_workspace_view', args=(path,)))
        else:
            destroy_workspace(User.objects.get(id=request.user.id), workspace_id)
            return HttpResponseRedirect(reverse('index_view'))
    else:
        orig_model, orig_workflow = open_workflow(User.objects.get(id=request.user.id), orig_workflow_id)
        crumbs = build_crumbs_from_path(m, '%s/save' % (path))
        return render_to_response('kepler/save_form.html', {'crumbs':crumbs, 'original': {'name': orig_model.name, 'public': orig_workflow.public}, 'next': reverse('save_workspace', args=(path,)), 'is_template':is_template }, context_instance=RequestContext(request))

def upload_workflow(request):
    if request.POST:
        if request.FILES:
            file = request.FILES.get('uri_file')
            try:
                print file
                m = ModelProxy(file.get('content'))
            except Exception, e:
                raise e
            workflow = request.POST.copy()
            workflow['name'] = unicode(m.name)
            workflow['owner'] = unicode(request.user.pk)
            d = time.localtime()
            workflow['created_date'] = unicode(time.strftime('%Y-%m-%d', d))
            workflow['created_time'] = unicode(time.strftime('%H:%M:%S', d))
            # generate new filename
            file['filename'] = md5.new('%s%s%s%s' % (request.user.username, m.name, file.get('content'), d)).hexdigest()
            workflow['uri_file'] = file

            add_new_workflow(workflow)
            msg = 'The workflow "%s" was uploaded successfully' % m.name
            request.user.message_set.create(message=msg)
            return HttpResponseRedirect(reverse('index_view'))
        else:
            raise Http404('''post without files, shouldn't happen''')
    else:
        return render_to_response('kepler/upload_workflow.html', {'title': _('Upload Workflow')}, context_instance=RequestContext(request))
upload_workflow = login_required(upload_workflow)

def delete_workflow(request, path):
    p = path.split('/')
    workflow_id = p[0]
    user = User.objects.get(id=request.user.id)
    model, wm = open_workflow(user, workflow_id)
    if wm.owner != user:
        # the message here doesn't actually get passed. TODO: fix it
        raise PermissionDenied('''you don't have permission to delete this workflow: you are not the owner''')
    if request.POST:
        dwf(user, workflow_id)
        msg = 'The workflow "%s" was deleted successfully' % model.name
        request.user.message_set.create(message=msg)
        return HttpResponseRedirect(reverse('index_view'))
    workflow = { 'name': wm.name }
    crumbs = build_crumbs_from_path(model, '%s/delete' % (path))
    return render_to_response('kepler/delete_confirmation.html', {'crumbs':crumbs, 'workflow': workflow}, context_instance=RequestContext(request))
delete_workflow = login_required(delete_workflow)

def close_workspace(request, path):
    p = path.split('/')
    workspace_id = p[0]
    user = User.objects.get(id=request.user.id)
    model = get_model_from_workspace(user, workspace_id)
    if request.POST:
        destroy_workspace(user, workspace_id)
        msg = 'The workspace for "%s" was closed successfully' % model.name
        request.user.message_set.create(message=msg)
        return HttpResponseRedirect(reverse('index_view'))
    workspace = { 'name': model.name }
    crumbs = build_crumbs_from_path(model, '%s/close' % (path))
    return render_to_response('kepler/close_confirmation.html', {'crumbs':crumbs, 'workspace': workspace}, context_instance=RequestContext(request))
close_workspace = login_required(close_workspace)

def delete_template(request, template_id):
    user = User.objects.get(id=request.user.id)
    template = get_object_or_404(Template, pk=template_id)
    if request.POST:
        if user != template.owner:
            raise PermissionDenied
        name = template.name
        template.delete()
        request.user.message_set.create(message='the template "%s" was deleted successfully' % name)
        return HttpResponseRedirect(reverse('index_view'))
    crumbs = {}
    return render_to_response('kepler/delete_template_confirmation.html', {'crumbs':crumbs, 'template': template}, context_instance=RequestContext(request))
delete_template = login_required(delete_template)

def edit_template(request, template_id):
    workspace_id = create_workspace(request.user, None, True, template_id)
    request.user.message_set.create(message='workspace to edit template opened successfully')
    return HttpResponseRedirect(reverse('portal_workspace_view', args=(workspace_id,)))
edit_template = login_required(edit_template)

def render_template(request, template_id):
    template = get_object_or_404(Template, pk=template_id)
    nodes = template.get_all_nodes()
    if request.POST:
        if request.POST.has_key('_cancel'):
            return HttpResponseRedirect(reverse('index_view'))
        raise Http404('not yet implemented')
    crumbs = {}
    return render_to_response('kepler/template.html', {'title': _(template.name), 'crumbs':crumbs, 'template': template, 'fields': nodes}, context_instance=RequestContext(request))
render_template = login_required(render_template)
