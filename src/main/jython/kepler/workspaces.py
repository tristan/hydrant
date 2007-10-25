import sys, dircache, md5, time, urllib, os, copy

from settings import MEDIA_ROOT
from django.utils import simplejson
from workflow.proxy import *
from workflow.cache import *
from models import Template, TemplateNode
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

STORE_PATH = MEDIA_ROOT + '/workspaces'

"""
workspaces are a memory resident version of a workflow which can be modified by the user who opened the instance
{
   username :
      {
          __lastusedid__: number,
          ws_id:   {
                        'model': model,
                        'workflow': Workflow object
                        'is_template': boolean,
                        {% if is_template %}
                        'template': Template object,
                        'nodes': { 'actor_path': TemplateNode },
                        {% endif %}
          }
      }
}

NOTE: to keep things simple, 1 workspace per user for now
"""

workspace_cache = {}

def get_model_from_workspace(user, workspace_id):
    """
    get the model associated with a specific workspace
    requires inputs:
        username: the user that owns the workspace (not sure if this is nessesary yet)
    """
    global workspace_cache
    if workspace_cache.has_key(user.id) and workspace_cache[user.id].has_key(workspace_id):
        return workspace_cache[user.id][workspace_id]['model']
    else:
        raise Exception('workspace with id "%s" does not exist for user "%s"' % (workspace_id, user.username))


def get_original_workflow_id(user, workspace_id):
    global workspace_cache
    if workspace_cache.has_key(user.id) and workspace_cache[user.id].has_key(workspace_id):
        workflow = workspace_cache[user.id][workspace_id]['workflow']
        return workflow.id
    else:
        raise Exception('workspace with id "%s" does not exist for user "%s"' % (workspace_id, user.username))

def list_active_workspaces(user):
    """
    lists the active workspaces that the current user has opened
    """
    global workspace_cache
    if workspace_cache.has_key(user.id):
        list = []
        for i in workspace_cache[user.id].keys():
            if i == '__lastusedid__':
                pass
            else:
                d = workspace_cache[user.id][i]
                list.append({'name': d['model'].name, 'id': i, 'is_template': d['is_template']})
        return list
    else:
        return {}

def create_workspace(user, workflow_id, template=False, template_id=None):
    """
    creates a new workspace for user, opening an instance of the workflow for editing
    """
    global workspace_cache
    if user.is_authenticated():
        uo = User.objects.get(id=user.id)
    else:
        raise PermissionDenied('''anonymous user can't create workspaces''')
    username = user.username
    if not workspace_cache.has_key(user.id):
        workspace_cache[user.id] = {'__lastusedid__':0}
    workspace_id = workspace_cache[user.id]['__lastusedid__'] = workspace_cache[user.id]['__lastusedid__'] + 1
    workspace_id = str(workspace_id)
    if template is False or template_id is None:
        print 'OPEN_WORKFLOW: %s' % workflow_id
        model, workflow = open_workflow(uo, workflow_id)
        print workflow
    if template:
        if template_id:
            t = get_object_or_404(Template, pk=template_id)
            nodes = {}
            q_nodes = t.get_all_nodes()
            for n in t.get_all_nodes():
                nodes[n.property_id] = n
            workflow = t.workflow
            model = open_workflow_from_object(uo, workflow)[0]
        else:
            t = Template(workflow=workflow, owner=uo, public=False, description='')
            nodes = {}
    else:
        model = copy.copy(model)
        t = None
        nodes = {}
    workspace_cache[user.id][workspace_id] = {'model': model, 'workflow': workflow, 'is_template': template, 'template':t, 'nodes':nodes}
    return workspace_id

def is_templating_workspace(user, workspace_id):
    global workspace_cache
    if workspace_cache.has_key(user.id) and workspace_cache[user.id].has_key(workspace_id):
        return workspace_cache[user.id][workspace_id]['is_template']
    else:
        raise Exception('workspace with id "%s" does not exist for user "%s"' % (workspace_id, user.username))

def get_template_from_workspace(user, workspace_id):
    global workspace_cache
    if workspace_cache.has_key(user.id) and workspace_cache[user.id].has_key(workspace_id) and workspace_cache[user.id][workspace_id]['is_template']:
        return workspace_cache[user.id][workspace_id]['template']
    else:
        raise Exception('workspace "%s" is not a template' % (workspace_id, user.username))

def get_node_with_id(user, workspace_id, node_id):
    global workspace_cache
    if workspace_cache.has_key(user.id) and workspace_cache[user.id].has_key(workspace_id) and workspace_cache[user.id][workspace_id]['is_template']:
        nodes = workspace_cache[user.id][workspace_id]['nodes']
        if nodes.has_key(node_id):
            return nodes.get(node_id)
        else:
            return None
    else:
        raise Exception('error!')

def add_new_node(user, workspace_id, node_id, node):
    global workspace_cache
    if workspace_cache.has_key(user.id) and workspace_cache[user.id].has_key(workspace_id) and workspace_cache[user.id][workspace_id]['is_template']:
        nodes = workspace_cache[user.id][workspace_id]['nodes']
        nodes[node_id] = node
    else:
        raise Exception('error!')

def save_templating_workspace(user, workspace_id, name, public, overwrite):
    if workspace_cache.has_key(user.id) and workspace_cache[user.id].has_key(workspace_id) and workspace_cache[user.id][workspace_id]['is_template']:
        template = workspace_cache[user.id][workspace_id]['template']
        nodes = workspace_cache[user.id][workspace_id]['nodes']
        if not overwrite:
            template.id = None # reset the id so a new instance is saved
        template.name = name
        template.public = public
        template.save()
        for n in nodes:
            node = nodes.get(n)
            if not overwrite:
                node.id = None # reset the id so a new instance is saved
            node.template = template
            node.save()
    else:
        raise Exception('error!')

# TODO: much error checking
def destroy_workspace(user, workspace_id):
    global workspace_cache
    del workspace_cache[user.id][workspace_id]
