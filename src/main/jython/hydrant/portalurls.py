from django.conf.urls.defaults import *
from portalviews import *

urlpatterns = patterns('hydrant.portalviews',
    # Example:
    # (r'^kepler/', include('kepler.foo.urls')),

    # Uncomment this for admin:
    url(r'^$', 'home', name='home'),
    url(r'^dashboard/$', 'home', name='dashboard'),
    url(r'^upload/$', 'upload_workflow', name='upload_workflow'),
    url(r'^workflow/delete/([\w]+)/$', 'delete_workflow', name='delete_workflow'),
    url(r'^workflow/copy/([\w]+)/$', 'duplicate_workflow', name='duplicate_workflow'),
    url(r'^workflow/download/([\w]+)/$', 'download_workflow', name='download_workflow'),
    url(r'^workflow/([\w]+)/$', 'workflow', name='workflow'),
    url(r'^workflow/([\w]+)/([\w /]+)/$', 'workflow', name='workflow'),
    url(r'^job/create/([\w]+)/$', 'job_create', name='job_create'),
    url(r'^job/([\w]+)/$', 'job', name='job'),
    url(r'^job/([\w]+)/([\w]+)/$', 'job_media', name='serve_job_media'),
    url(r'^workflows/$', 'workflows', name='workflows'),
    url(r'^jobs/$', 'jobs', name='jobs'),
    url(r'^intro/$', 'intro', name='intro'),
    url(r'^([\w]+)/$', 'profile',name='profile'),
)
