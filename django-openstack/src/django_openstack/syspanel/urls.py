from django.conf.urls.defaults import *
from django.conf import settings

INSTANCES = r'^instances/(?P<instance_id>[^/]+)/%s$'

urlpatterns = patterns('django_openstack.syspanel.views.instances',
    url(r'^usage/(?P<tenant_id>[^/]+)$', 'tenant_usage',
        name='syspanel_tenant_usage'),
    url(r'^instances/$', 'index', name='syspanel_instances'),
    # NOTE(termie): currently just using the 'dash' versions
    #url(INSTANCES % 'console', 'console', name='syspanel_instances_console'),
    #url(INSTANCES % 'vnc', 'vnc', name='syspanel_instances_vnc'),
)

urlpatterns += patterns('django_openstack.syspanel.views.images',
    url(r'^images/$', 'index', name='syspanel_images'),
    # NOTE(termie): currently just using the 'dash' versions
    #url(INSTANCES % 'console', 'console', name='syspanel_instances_console'),
    #url(INSTANCES % 'vnc', 'vnc', name='syspanel_instances_vnc'),
)

urlpatterns += patterns('django_openstack.syspanel.views.flavors',
    url(r'^flavors/$', 'index', name='syspanel_flavors'),
    url(r'^flavors/create/$', 'create', name='syspanel_flavors_create'),
)


urlpatterns_OLD = patterns('',
    url(r'^$', 'django_openstack.syspanel.views.home.index', name='syspanel_index'),

    # instances
    url(r'^instances/$', 'django_openstack.syspanel.views.instances.index', name='syspanel_instances'),
    url(r'^instances/(?P<instance_id>[^/]+)/terminate$', 'django_openstack.syspanel.views.instances.terminate', name='syspanel_instance_terminate'),
    url(r'^instances/(?P<instance_id>[^/]+)/restart$', 'django_openstack.syspanel.views.instances.restart', name='syspanel_instance_restart'),
    url(r'^instances/(?P<instance_id>[^/]+)/console_log$', 'django_openstack.syspanel.views.instances.console', name='syspanel_instance_console'),

    # volumes
    #url(r'^volumes/$', 'django_openstack.syspanel.views.volumes.index', name='syspanel_volumes'),
    #url(r'^volumes/(?P<volume_id>[^/]+)/delete$', 'django_openstack.syspanel.views.volumes.delete', name='syspanel_delete_volume'),
    #url(r'^volumes/(?P<volume_id>[^/]+)/detach$', 'django_openstack.syspanel.views.volumes.detach', name='syspanel_detach_volume'),

    # vpns
    url(r'^vpns/$', 'django_openstack.syspanel.views.vpns.index', name='syspanel_vpns'),
    url(r'^vpns/(?P<project_id>[^/]+)/launch$', 'django_openstack.syspanel.views.vpns.launch', name='syspanel_vpn_launch'),
    url(r'^vpns/(?P<project_id>[^/]+)/send_credentials$', 'django_openstack.syspanel.views.vpns.send_credentials', name='syspanel_vpn_send_credentials'),
    url(r'^vpns/(?P<project_id>[^/]+)/terminate$', 'django_openstack.syspanel.views.vpns.terminate', name='syspanel_vpn_terminate'),
    url(r'^vpns/(?P<project_id>[^/]+)/restart$', 'django_openstack.syspanel.views.vpns.restart', name='syspanel_vpn_restart'),
    url(r'^vpns/(?P<project_id>[^/]+)/console_log$', 'django_openstack.syspanel.views.vpns.console', name='syspanel_vpn_console'),

    # cloudview
    url(r'^cloudview/$', 'django_openstack.syspanel.views.cloud.index', name='syspanel_cloudview'),
)
