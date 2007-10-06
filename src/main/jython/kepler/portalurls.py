from django.conf.urls.defaults import *
from portalviews import *

urlpatterns = patterns('kepler.portalviews',
    # Example:
    # (r'^kepler/', include('kepler.foo.urls')),

    # Uncomment this for admin:
    url(r'^$', 'index', name='index_view'),
    url(r'^wf/([\w /]+)/properties/', 'properties', name='properties_div_view'),
    url(r'^wf/([\w /]+)/edit/', 'start_workflow_edit', name='start_edit'),
    url(r'^wf/([\w /]+)/template/', 'start_workflow_edit', {'template':True}, name='start_template'),
    url(r'^wf/([\w /]+)/delete/', 'delete_workflow', name='delete_workflow'),
    url(r'^wf/([\w /]+)/$', 'workflow', name='portal_workflow_view'),
    url(r'^ws/([\w /]+)/properties/', 'properties', {'is_workspace':True}, name='workspace_properties_div_view'),
    url(r'^ws/([\w /]+)/save/', 'save_workspace', name='save_workspace'),
    url(r'^ws/([\w /]+)/close/', 'close_workspace', name='close_workspace'),
    url(r'^ws/([\w /]+)/$', 'workflow', {'is_workspace':True}, name='portal_workspace_view'),
    url(r'^template/([\w /]+)/delete/', 'delete_template', name='delete_template'),
    url(r'^template/([\w /]+)/edit/', 'edit_template', name='edit_template'),
    url(r'^template/([\w /]+)/$', 'render_template', name='template_view'),
    url(r'^upload/$', 'upload_workflow', name='upload_workflow_view'),
    #(r'^save/(?P<id>[\.\w_-]+)', 'save'),
)
