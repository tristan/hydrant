from django.conf.urls.defaults import *

urlpatterns = patterns('kepler.backend.views',
    url(r'^$', 'index', name='index_view'),
    url(r'^list/$', 'workflowList', name='list'),
)
