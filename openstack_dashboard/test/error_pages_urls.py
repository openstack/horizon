from django.conf.urls import patterns

from openstack_dashboard.urls import urlpatterns

urlpatterns += patterns('',
    (r'^500/$', 'django.views.defaults.server_error')
)
