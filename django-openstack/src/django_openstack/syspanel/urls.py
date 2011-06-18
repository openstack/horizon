from django.conf.urls.defaults import *
from django.conf import settings


INSTANCES = r'^instances/(?P<instance_id>[^/]+)/%s$'
USERS = r'^users/(?P<user_id>[^/]+)/%s$'


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


urlpatterns += patterns('django_openstack.syspanel.views.users',
    url(r'^users/$', 'index', name='syspanel_users'),
    url(USERS % 'update', 'update', name='syspanel_users_update'),
    url(r'^users/create$', 'create', name='syspanel_users_create'),
)


urlpatterns += patterns('django_openstack.syspanel.views.services',
    url(r'^services/$', 'index', name='syspanel_services'),
)
