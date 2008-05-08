import traceback
from django.conf.urls.defaults import *
from django.http import HttpResponseRedirect
from settings import MEDIA_ROOT, ADMIN_MEDIA_ROOT, ROOT_URL, USE_HTTPS

try:
    urlpatterns = patterns(
        '',
        (r'^%smedia/workflows/(?P<path>.*)$' % ROOT_URL, 
         'hydrant.views.hide_workflows'),
        (r'^%smedia/(?P<path>.*)$' % ROOT_URL, 'django.views.static.serve', 
         {'document_root': MEDIA_ROOT, 'show_indexes': True}),
        (r'^%smediaadmin/(?P<path>.*)$' % ROOT_URL, 'django.views.static.serve', 
         {'document_root': ADMIN_MEDIA_ROOT, 'show_indexes': True}),
        (r'^%saccounts/login/$' % ROOT_URL, 'django.contrib.auth.views.login',
         {'template_name': 'login.html', 'SSL':USE_HTTPS}, 'login'),
        (r'^%saccounts/signup/$' % ROOT_URL, 'jython.hydrant.views.signup',
         {'SSL':USE_HTTPS}, 'signup'),
    (r'^%saccounts/logout/$' % ROOT_URL, 'django.contrib.auth.views.logout',
     {'next_page':'/%s' % ROOT_URL}, 'logout'),
        (r'^%sadmin/' % ROOT_URL, include('django.contrib.admin.urls')),
        #    (r'^%s$' % ROOT_URL, lambda request: HttpResponseRedirect('/%sportal/' % ROOT_URL)),
        url(r'^%sfaq/$' % ROOT_URL, 'django.views.generic.simple.direct_to_template',
            {'template': 'faq.html'}, name='faq'),
        url(r'^%sscreencast/$' % ROOT_URL, 'django.views.generic.simple.direct_to_template',
            {'template': 'screencast.html'}, name='screencast'),
        #    (r'^%sforum/' % ROOT_URL, include('forum.urls')),
        (r'^%s' % ROOT_URL, include('jython.hydrant.urls')),        
    )
except:
    traceback.print_exc()
    raise
