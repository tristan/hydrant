from django.conf.urls.defaults import *

urlpatterns = patterns('kepler.webportal.views',
    url(r'^$', 'index', name='index_view'),
    url(r'^workflow/(?P<workflow_id>[\w_-]+)/$', 'workflow', name='workflow_view'),
    url(r'^workflow/(?P<workflow_id>[\w_-]+)/composite(?P<actor_path>[\w/-]+)/$', 'composite', name='composite_view'),
)
