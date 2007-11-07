from django.conf.urls.defaults import *
from settings import MEDIA_ROOT, ROOT_URL

urlpatterns = patterns('',
    (r'^%smedia/(?P<path>.*)$' % ROOT_URL, 'django.views.static.serve', {'document_root': MEDIA_ROOT, 'show_indexes': True}),
    (r'^%saccounts/login/$' % ROOT_URL, 'django.contrib.auth.views.login', {'template_name': 'kepler/login.html'}, 'login_view'),
    (r'^%saccounts/logout/$' % ROOT_URL, 'django.contrib.auth.views.logout', {'template_name': 'kepler/logout.html'}, 'logout_view'),
    #(r'^kepler/', include('jython.kepler.urls')),
    (r'^%sportal/' % ROOT_URL, include('jython.kepler.portalurls')),
    (r'^%sadmin/' % ROOT_URL, include('django.contrib.admin.urls')),
)