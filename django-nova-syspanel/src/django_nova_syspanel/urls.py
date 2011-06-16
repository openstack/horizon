from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'django_nova_syspanel.views.home.index', name='syspanel_index'),
    url(r'^instances/$', 'django_nova_syspanel.views.instances.index', name='syspanel_instances'),
    url(r'^instances/(?P<instance_id>[^/]+)/terminate$', 'django_nova_syspanel.views.instances.terminate', name='syspanel_instance_terminate'),
    url(r'^instances/(?P<instance_id>[^/]+)/restart$', 'django_nova_syspanel.views.instances.restart', name='syspanel_instance_restart'),
    url(r'^instances/(?P<instance_id>[^/]+)/console_log$', 'django_nova_syspanel.views.instances.console', name='syspanel_instance_console'),

    url(r'^volumes/$', 'django_nova_syspanel.views.volumes.index', name='syspanel_volumes'),
    url(r'^volumes/(?P<volume_id>[^/]+)/delete$', 'django_nova_syspanel.views.volumes.delete', name='syspanel_delete_volume'),
    url(r'^volumes/(?P<volume_id>[^/]+)/detach$', 'django_nova_syspanel.views.volumes.detach', name='syspanel_detach_volume'),

    url(r'^security/$', 'django_nova_syspanel.views.security.index', name='syspanel_security'),
    url(r'^security/disable_project_credentials/$', 'django_nova_syspanel.views.security.disable_project_credentials', name='syspanel_security_disable_project_credentials'),
    url(r'^security/disable_ip_range/$', 'django_nova_syspanel.views.security.disable_ip', name='syspanel_security_disable_ip_range'),
    url(r'^security/disable_public_ips/$', 'django_nova_syspanel.views.security.disable_public_ips', name='syspanel_security_disable_public_ips'),
    url(r'^security/disable_vpn/$', 'django_nova_syspanel.views.security.disable_vpn', name='syspanel_security_disable_vpn'),

    url(r'^vpns/$', 'django_nova_syspanel.views.vpns.index', name='syspanel_vpns'),
    url(r'^vpns/(?P<project_id>[^/]+)/launch$', 'django_nova_syspanel.views.vpns.launch', name='syspanel_vpn_launch'),
    url(r'^vpns/(?P<project_id>[^/]+)/send_credentials$', 'django_nova_syspanel.views.vpns.send_credentials', name='syspanel_vpn_send_credentials'),
    url(r'^vpns/(?P<project_id>[^/]+)/terminate$', 'django_nova_syspanel.views.vpns.terminate', name='syspanel_vpn_terminate'),
    url(r'^vpns/(?P<project_id>[^/]+)/restart$', 'django_nova_syspanel.views.vpns.restart', name='syspanel_vpn_restart'),
    url(r'^vpns/(?P<project_id>[^/]+)/console_log$', 'django_nova_syspanel.views.vpns.console', name='syspanel_vpn_console'),

    url(r'^cloudview/$', 'django_nova_syspanel.views.cloud.index', name='syspanel_cloudview'),
)
