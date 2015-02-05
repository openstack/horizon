from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.idm_admin.notify import views


urlpatterns = patterns('',
    url(r'^$', views.NotifyEmailView.as_view(), name='index'),
)
