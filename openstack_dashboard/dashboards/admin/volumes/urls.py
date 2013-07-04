from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url

from openstack_dashboard.dashboards.admin.volumes.views \
    import CreateVolumeTypeView
from openstack_dashboard.dashboards.admin.volumes.views import DetailView
from openstack_dashboard.dashboards.admin.volumes.views import IndexView

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^create_type$', CreateVolumeTypeView.as_view(), name='create_type'),
    url(r'^(?P<volume_id>[^/]+)/$', DetailView.as_view(), name='detail'),
)
