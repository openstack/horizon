from django.conf.urls import patterns  # noqa

from openstack_dashboard.urls import urlpatterns  # noqa

urlpatterns += patterns('',
    (r'^500/$', 'django.views.defaults.server_error')
)
