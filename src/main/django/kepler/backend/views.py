# Create your views here.
from django.http import Http404, HttpResponse
from kepler.settings import MEDIA_ROOT
from kepler.backend.models import *
from kepler.backend import storage
from django.utils import simplejson

def index(request):
    return HttpResponse('<h1>HI!</h1>')

def workflowList(request):
    data = simplejson.dumps({'workflows': storage.listWorkflows()})
    return HttpResponse(data)