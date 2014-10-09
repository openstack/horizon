from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.idm.myApplications \
		import views


urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(r'^upload/$', views.UploadImageView.as_view(), name='upload'),
    url(r'^roles/$', views.RolesView.as_view(), name='roles'),
)
