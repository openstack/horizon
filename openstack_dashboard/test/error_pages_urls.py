from django.conf.urls import url
from django.views import defaults

from openstack_dashboard.urls import urlpatterns  # noqa

urlpatterns.append(url(r'^500/$', defaults.server_error))
