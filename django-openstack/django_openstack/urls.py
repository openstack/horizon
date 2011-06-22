# vim: tabstop=4 shiftwidth=4 softtabstop=4

from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    url(r'^auth/', include('django_openstack.auth.urls')),
    url(r'^dash/', include('django_openstack.dash.urls')),
    url(r'^syspanel/', include('django_openstack.syspanel.urls')),
)
