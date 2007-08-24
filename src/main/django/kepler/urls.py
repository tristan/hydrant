from django.conf.urls.defaults import *
from settings import MEDIA_ROOT

urlpatterns = patterns('',
    # Example:
    # (r'^kepler/', include('kepler.foo.urls')),

    # Uncomment this for admin:
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': MEDIA_ROOT, 'show_indexes': True}),
    (r'^admin/', include('django.contrib.admin.urls')),
    (r'^webportal/', include('kepler.webportal.urls')),
    (r'^backend/', include('kepler.backend.urls')),
)