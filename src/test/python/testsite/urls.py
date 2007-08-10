from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    # (r'^testsite/', include('testsite.foo.urls')),

    # Uncomment this for admin:
    (r'^admin/', include('django.contrib.admin.urls')),
    (r'^polls/', include('testsite.polls.urls')),
)
