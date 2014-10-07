from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.idm.myApplications \
		import views


urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^create/$', views.CreateView.as_view(), name='create'),
)
