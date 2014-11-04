from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.idm.organizations import views

urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^create/$', views.CreateOrganizationView.as_view(), name='create'),
    url(r'^(?P<organization_id>[^/]+)/$', views.DetailOrganizationView.as_view(), name='detail'), 
    url(r'^(?P<organization_id>[^/]+)/edit/$', views.MultiFormView.as_view(), name='edit'), 
    url(r'^(?P<organization_id>[^/]+)/edit/url1/$', views.InfoFormView.as_view(), name='info'),
    # url(r'^url2/$', views.ContactFormView.as_view(), name='contact'),
    # url(r'^url3/$', views.AvatarFormView.as_view(), name='avatar'),
    # url(r'^url4/$', views.CancelFormView.as_view(), name='cancel'),
)
