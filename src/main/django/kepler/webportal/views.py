# Create your views here.
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse
from models import *
from kepler.settings import PROJECT_HOME, MEDIA_ROOT
from django.core import serializers
from django.utils import simplejson

workflows = {'plottest':'/media/workflows/plottest.xml',
             'jainis-JCU-tester': '/media/workflows/jainis-JCU-tester.xml',
             'lotsOfLevels': '/media/workflows/lotsOfLevels.xml',
             }

WORKFLOW_PATH = MEDIA_ROOT + '/workflows/'

def index(request):
    return render_to_response('webportal/index.html', {'results':listWorkflows()})

def workflow(request, workflow_id, composite_path=''):
    results = viewWorkflow(workflow_id, composite_path)
    if 'result' in results.keys() and results['result'] is 0:
        return render_to_response('webportal/missing.html', {'results':results})
    return render_to_response('webportal/workflow.html', {'results':results})

def proxy(request, url):
    return render_to_response('webportal/base.html', {'results':proxycall(url)})

def properties(request, workflow_id, actor_path, type='actor'):
#    workflow = [wf for wf in listWorkflows(WORKFLOW_PATH) if wf['name']==workflow_id][0]
#    actor = getProperties(WORKFLOW_PATH + workflow['path'], actor_path)
    results = getProperties(workflow_id, actor_path)
    if 'result' in results.keys() and results['result'] is 0:
        return Http404()
    return render_to_response('webportal/properties.html', {'actor':results['actor']})