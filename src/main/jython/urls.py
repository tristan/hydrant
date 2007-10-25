from django.conf.urls.defaults import *
from settings import MEDIA_ROOT

urlpatterns = patterns('',
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': MEDIA_ROOT, 'show_indexes': True}),
    (r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'kepler/login.html'}, 'login_view'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'template_name': 'kepler/logout.html'}, 'logout_view'),
    #(r'^kepler/', include('jython.kepler.urls')),
    (r'^portal/', include('jython.kepler.portalurls')),
    (r'^admin/', include('django.contrib.admin.urls')),
)
