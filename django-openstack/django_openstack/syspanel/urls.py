from django.conf.urls.defaults import *
from django.conf import settings


INSTANCES = r'^instances/(?P<instance_id>[^/]+)/%s$'
IMAGES = r'^images/(?P<image_id>[^/]+)/%s$'
USERS = r'^users/(?P<user_id>[^/]+)/%s$'
TENANTS = r'^tenants/(?P<tenant_id>[^/]+)/%s$'


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
    url(r'^images/upload/$', 'upload', name='syspanel_images_upload'),
    url(IMAGES % 'update', 'update', name='syspanel_images_update'),
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


urlpatterns += patterns('django_openstack.syspanel.views.tenants',
    url(r'^tenants/$', 'index', name='syspanel_tenants'),
    url(TENANTS % 'update', 'update', name='syspanel_tenant_update'),
    url(TENANTS % 'users', 'users', name='syspanel_tenant_users'),
    url(r'^tenants/create$', 'create', name='syspanel_tenants_create'),
)
