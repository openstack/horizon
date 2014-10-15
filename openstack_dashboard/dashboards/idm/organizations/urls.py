from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.idm.organizations import views

urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^create/$', views.CreateOrganizationView.as_view(), name='create'),
    url(r'^(?P<organization_id>[^/]+)/$', views.DetailOrganizationView.as_view(), name='detail'), 
    url(r'^(?P<organization_id>[^/]+)/edit/$', views.EditOrganizationView.as_view(), name='edit'), 
)
