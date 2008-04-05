from django.conf.urls.defaults import *
from django.http import HttpResponseRedirect
from settings import MEDIA_ROOT, ROOT_URL

urlpatterns = patterns('',
    (r'^%smedia/workflows/(?P<path>.*)$' % ROOT_URL, 
     'kepler.portalviews.hide_workflows'),
    (r'^%smedia/(?P<path>.*)$' % ROOT_URL, 'django.views.static.serve', 
     {'document_root': MEDIA_ROOT, 'show_indexes': True}),
    (r'^%saccounts/login/$' % ROOT_URL, 'django.contrib.auth.views.login',
     {'template_name': 'kepler/login.html'}, 'login_view'),
    (r'^%saccounts/logout/$' % ROOT_URL, 'django.contrib.auth.views.logout',
     {'template_name': 'kepler/logout.html'}, 'logout_view'),
    (r'^%sportal/' % ROOT_URL, include('jython.hydrant.portalurls')),
    (r'^%sadmin/' % ROOT_URL, include('django.contrib.admin.urls')),
    (r'^%s$' % ROOT_URL, lambda request: HttpResponseRedirect('/%sportal/' % ROOT_URL)),
)
