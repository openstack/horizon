from boto.exception import EC2ResponseError
from django import template
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render_to_response
from django.utils.translation import ugettext as _

from django_nova_syspanel.models import *


@login_required
def index(request):
    nova = get_nova_admin_connection()
    conn = nova.connection_for(settings.NOVA_ADMIN_USER, settings.NOVA_PROJECT)
    volumes = conn.get_all_volumes()

    for volume in volumes:
        statusstr = str(volume.status)[:-1]
        instance = statusstr.split(', ')[-2]
        device = statusstr.split(', ')[-1]
        status = statusstr.split(' ')[0]

        volume.device = device
        volume.instance = instance
        volume.status_str = status

    return render_to_response('django_nova_syspanel/volumes/index.html',
                             {'volumes': volumes, },
                             context_instance=template.RequestContext(request))


@login_required
def detach(request, volume_id):
    nova = get_nova_admin_connection()
    conn = nova.connection_for(settings.NOVA_ADMIN_USER, settings.NOVA_PROJECT)
    try:
        conn.detach_volume(volume_id)
    except EC2ResponseError, e:
        messages.error(request, 'Unable to detach volume %s: %s' % \
                                (volume_id, e.error_message))
    else:
        messages.success(request,
                         _('Volume %s has been scheduled to be detached.') %
                         volume_id)
    return redirect('syspanel_volumes')


@login_required
def delete(request, volume_id):
    nova = get_nova_admin_connection()
    conn = nova.connection_for(settings.NOVA_ADMIN_USER, settings.NOVA_PROJECT)
    try:
        conn.delete_volume(volume_id)
    except EC2ResponseError, e:
        messages.error(request,
                       _('Unable to delete volume %(vol)s: %(msg)s') %
                        {'vol': volume_id, 'msg': e.error_message})
    else:
        messages.success(request,
                         _('Volume %s has been successfully deleted.') %
                         volume_id)
    return redirect('syspanel_volumes')
