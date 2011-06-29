# vim: tabstop=4 shiftwidth=4 softtabstop=4

from django.conf.urls.defaults import *

INSTANCES = r'^(?P<tenant_id>[^/]+)/instances/(?P<instance_id>[^/]+)/%s$'
IMAGES = r'^(?P<tenant_id>[^/]+)/images/(?P<image_id>[^/]+)/%s$'
KEYPAIRS = r'^(?P<tenant_id>[^/]+)/keypairs/%s$'
CONTAINERS = r'^(?P<tenant_id>[^/]+)/containers/%s$'
OBJECTS = r'^(?P<tenant_id>[^/]+)/containers/(?P<container_name>[^/]+)/%s$'

urlpatterns = patterns('django_openstack.dash.views.instances',
    url(r'^(?P<tenant_id>[^/]+)/$', 'usage', name='dash_usage'),
    url(r'^(?P<tenant_id>[^/]+)/instances/$', 'index', name='dash_instances'),
    url(INSTANCES % 'console', 'console', name='dash_instances_console'),
    url(INSTANCES % 'vnc', 'vnc', name='dash_instances_vnc'),
)

urlpatterns += patterns('django_openstack.dash.views.images',
    url(r'^(?P<tenant_id>[^/]+)/images/$', 'index', name='dash_images'),
    url(IMAGES % 'launch', 'launch', name='dash_images_launch'),
)

urlpatterns += patterns('django_openstack.dash.views.keypairs',
    url(r'^(?P<tenant_id>[^/]+)/keypairs/$', 'index', name='dash_keypairs'),
    url(KEYPAIRS % 'create', 'create', name='dash_keypairs_create'),
)

# Swift containers and objects.
urlpatterns += patterns('django_openstack.dash.views.containers',
    url(CONTAINERS % '', 'index', name='dash_containers'),
    url(CONTAINERS % 'create', 'create', name='dash_containers_create'),
)

urlpatterns += patterns('django_openstack.dash.views.objects',
    url(OBJECTS % '', 'index', name='dash_objects'),
    url(OBJECTS % 'upload', 'upload', name='dash_objects_upload'),
    url(OBJECTS % '(?P<object_name>[^/]+)/download',
        'download', name='dash_objects_download'),
)
