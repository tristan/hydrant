from django.conf.urls.defaults import *

urlpatterns = patterns('kepler.webportal.views',
    url(r'^$', 'index', name='index_view'),
    url(r'^proxy/(?P<url>[\.\w\ /-]+)$', 'proxy', name='proxy_view'),
    url(r'^workflow/(?P<workflow_id>[\w_-]+)/$', 'workflow', name='workflow_view'),
    url(r'^workflow/(?P<workflow_id>[\w_-]+)/composite(?P<composite_path>[\w/-]+)/$', 'workflow', name='composite_view'),
    url(r'^workflow/(?P<workflow_id>[\w_-]+)/properties/(?P<actor_path>[\w\ /-]+)/$', 'properties', name='properties_view'),
)
