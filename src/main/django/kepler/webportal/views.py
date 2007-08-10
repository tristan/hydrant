# Create your views here.
from django.shortcuts import render_to_response
from django.http import Http404
from models import *
from kepler.settings import PROJECT_HOME

workflows = {'plottest':'/media/workflows/plottest.xml',
             'jainis-JCU-tester': '/media/workflows/jainis-JCU-tester.xml',
             'lotsOfLevels': '/media/workflows/lotsOfLevels.xml',
             }

def index(request):
    return render_to_response('webportal/index.html', {'workflows':workflows})

def workflow(request, workflow_id):
    try:
        wf = getWorkflow(PROJECT_HOME + workflows[workflow_id])
    except:
        raise Http404
    return render_to_response('webportal/workflow.html', {'workflow':wf})

def composite(request, workflow_id, actor_path):
    if workflow_id == 'plottest':
        wf = getCompositeActor(PROJECT_HOME + '/media/workflows/plottest.xml', actor_path)
    elif workflow_id == 'jainis-JCU-tester':
        wf = getCompositeActor(PROJECT_HOME + '/media/workflows/jainis-JCU-tester.xml', actor_path)
    elif workflow_id == 'lotsOfLevels':
        wf = getCompositeActor(PROJECT_HOME + '/media/workflows/lotsOfLevels.xml', actor_path)
    return render_to_response('webportal/workflow.html', {'workflow':wf})