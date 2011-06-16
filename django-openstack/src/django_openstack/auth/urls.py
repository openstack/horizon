# vim: tabstop=4 shiftwidth=4 softtabstop=4

from django.conf.urls.defaults import *
from django.conf import settings


urlpatterns = patterns('django_openstack.auth.views',
    url(r'login/$', 'login', name='auth_login'),
    url(r'logout/$', 'logout', name='auth_logout'),
    url(r'switch/(?P<tenant_id>[^/]+)/$', 'switch_tenants', name='auth_switch'),
)

