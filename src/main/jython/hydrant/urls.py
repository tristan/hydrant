from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('hydrant.views',
    # Example:
    # (r'^kepler/', include('kepler.foo.urls')),

    # Uncomment this for admin:
    url(r'^$', 'home', name='home'),
    url(r'^dashboard/$', 'home', name='dashboard'),
    url(r'^about/$', 'intro', name='about'),
    url(r'^upload/$', 'upload_workflow', name='upload_workflow'),
    url(r'^workflow/delete/([\w]+)/$', 'delete_workflow', name='delete_workflow'),
    url(r'^workflow/undelete/([\w]+)/$', 'delete_workflow', {'undelete':True}, name='undelete_workflow'),
    url(r'^workflow/copy/([\w]+)/$', 'duplicate_workflow', name='duplicate_workflow'),
    url(r'^workflow/download/([\w]+)/$', 'download_workflow', name='download_workflow'),
    url(r'^workflow/([\w]+)/$', 'workflow', name='workflow'),
    url(r'^workflow/([\w]+)/([\w /]+)/$', 'workflow', name='workflow'),
    url(r'^job/create/([\w]+)/$', 'job_create', name='job_create'),
    url(r'^job/rerun/([\w]+)/$', 'job_rerun', name='job_rerun'),
    url(r'^job/stop/([\w]+)/$', 'job_stop', name='job_stop'),
    url(r'^job/([\w]+)/$', 'job', name='job'),
    url(r'^job/([\w]+)/([\w]+)/$', 'job_media', name='serve_job_media'),
    url(r'^workflows/$', 'workflows', name='workflows'),
    url(r'^jobs/$', 'jobs', name='jobs'),
    url(r'^user/([\w]+)/$', 'profile',name='profile'),
)
