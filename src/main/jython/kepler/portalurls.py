from django.conf.urls.defaults import *
from portalviews import *

urlpatterns = patterns('kepler.portalviews',
    # Example:
    # (r'^kepler/', include('kepler.foo.urls')),

    # Uncomment this for admin:
    url(r'^$', 'welcome', name='welcome'),
    url(r'^dashboard/$', 'dashboard', name='dashboard'),
    url(r'^upload/$', 'upload_workflow', name='upload_workflow'),
    url(r'^workflow/delete/([\w]+)/$', 'delete_workflow', name='delete_workflow'),
    url(r'^workflow/copy/([\w]+)/$', 'duplicate_workflow', name='duplicate_workflow'),
    url(r'^workflow/download/([\w]+)/$', 'download_workflow', name='download_workflow'),
    url(r'^workflow/([\w]+)/$', 'workflow', name='workflow_view'),
    url(r'^model/([\w /]+)/$', 'model', name='model_view'),
    url(r'^properties/([\w]+)/$', 'properties', name='properties'),
    url(r'^parameters/([\w /]+)/$', 'parameters', name='parameters'),
    url(r'^jobform/([\w]+)/$', 'job_form', name='job_form_view'),
    url(r'^job/([\w]+)/$', 'job_details', name='job_details_view'),
    url(r'^job/([\w]+)/([\w]+)/$', 'job_media', name='serve_job_media'),
    url(r'^workflows/$', 'workflows', name='workflows'),
    url(r'^jobs/$', 'jobs', name='jobs'),
)
