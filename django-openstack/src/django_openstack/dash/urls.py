# vim: tabstop=4 shiftwidth=4 softtabstop=4

from django.conf.urls.defaults import *
from django.conf import settings

INSTANCES = r'^(?P<tenant_id>[^/]+)/instances/(?P<instance_id>[^/]+)/%s$'
IMAGES = r'^(?P<tenant_id>[^/]+)/images/(?P<image_id>[^/]+)/%s$'

urlpatterns = patterns('django_openstack.dash.views.instances',
    url(r'^(?P<tenant_id>[^/]+)/instances/$', 'index', name='dash_instances'),
    url(INSTANCES % 'terminate', 'terminate', name='dash_instances_terminate'),
    url(INSTANCES % 'reboot', 'reboot', name='dash_instances_reboot'),
    url(INSTANCES % 'console', 'console', name='dash_instances_console'),
    url(INSTANCES % 'vnc', 'vnc', name='dash_instances_vnc'),
    #url(INSTANCES % '', 'detail', name='dash_instances_detail'),
)

urlpatterns += patterns('django_openstack.dash.views.images',
    url(r'^(?P<tenant_id>[^/]+)/images/$', 'index', name='dash_images'),
    url(r'^(?P<tenant_id>[^/]+)/images/upload/$',
        'upload',
        name='dash_images_upload'),
    url(IMAGES % 'launch', 'launch', name='dash_images_launch'),

    #url(r'^(?P<tenant_id>[^/]+)/images/(?P<image_id>[^/]+)/update$',
    #    'update',
    #    name='dash_images_update'),
)
