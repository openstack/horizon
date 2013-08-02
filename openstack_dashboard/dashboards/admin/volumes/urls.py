from django.conf.urls.defaults import patterns  # noqa
from django.conf.urls.defaults import url  # noqa

from openstack_dashboard.dashboards.admin.volumes import views

urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^create_type$', views.CreateVolumeTypeView.as_view(),
        name='create_type'),
    url(r'^(?P<volume_id>[^/]+)/$', views.DetailView.as_view(), name='detail'),
)
