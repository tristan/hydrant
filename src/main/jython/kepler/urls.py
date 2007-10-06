from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('kepler.views',
    # Example:
    # (r'^kepler/', include('kepler.foo.urls')),

    # Uncomment this for admin:
    (r'^list/(?P<username>[\.\w_-]+)/$', 'list'),
    (r'^list/$', 'list'),
    (r'^properties/(?P<id>[\.\w_-]+)/(?P<path>[\w\ /-]+)/$', 'properties'),
    (r'^structure/(?P<id>[\.\w_-]+)/(?P<path>[\w\ /-]+)/$', 'structure'),
    (r'^structure/(?P<id>[\.\w_-]+)/$', 'structure'),
    (r'^open/(?P<id>[\.\w_-]+)', 'new_workspace'),
    #(r'^save/(?P<id>[\.\w_-]+)', 'save'),
    (r'^set/', 'set_property'),
)
