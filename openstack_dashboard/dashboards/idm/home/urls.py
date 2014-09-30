from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.idm.home import views
from openstack_dashboard.dashboards.idm.organizations import views as orgviews

urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^$', orgviews.IndexView.as_view(), name='organizations'),
   )
