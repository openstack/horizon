from django import template
from django import http
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _

from django_nova_syspanel.models import *


def _reservations_to_instances(reservation_list):
    rv = []
    for r in reservation_list:
        for i in r.instances:
            i2 = r.__dict__.copy()
            i2.update(i.__dict__)
            i2['host_name'] = i2['key_name'].split(', ')[1][:-1]
            i2['disks'] = []
            for point, drive in i.block_device_mapping.iteritems():
                i2['disks'].append({'path': point, 'id': drive.volume_id})
            rv.append(i2)
    return rv


@login_required
def index(request):
    nova = get_nova_admin_connection()
    conn = nova.connection_for(settings.NOVA_ADMIN_USER, settings.NOVA_PROJECT)
    reservations = conn.get_all_instances()
    instances = _reservations_to_instances(reservations)
    return render_to_response('django_nova_syspanel/instances/index.html',
                             {'instances': instances, },
                             context_instance=template.RequestContext(request))


@login_required
def terminate(request, instance_id):
    nova = get_nova_admin_connection()
    conn = nova.connection_for(settings.NOVA_ADMIN_USER, settings.NOVA_PROJECT)
    reservations = conn.get_all_instances()
    instances = _reservations_to_instances(reservations)
    try:
        conn.terminate_instances([instance_id])
        message = _("Instance %s has been scheduled for termination.") % \
                  instance_id
        status = "success"
    except:
        message = _("There were issues trying to terminate instance %s.  "
                  "Please try again.") % instance_id
        status = "error"
    # reload instances, maybe get new state
    reservations = conn.get_all_instances()
    instances = _reservations_to_instances(reservations)
    return render_to_response('django_nova_syspanel/instances/index.html',
                             {'instances': instances,
                               'message': message,
                               'status': status, },
                             context_instance=template.RequestContext(request))


@login_required
def console(request, instance_id):
    nova = get_nova_admin_connection()
    conn = nova.connection_for(settings.NOVA_ADMIN_USER, settings.NOVA_PROJECT)
    console = conn.get_console_output(instance_id)
    response = http.HttpResponse(mimetype='text/plain')
    response.write(console.output)
    response.flush()

    return response


@login_required
def restart(request, instance_id):
    nova = get_nova_admin_connection()
    conn = nova.connection_for(settings.NOVA_ADMIN_USER, settings.NOVA_PROJECT)
    try:
        conn.reboot_instances([instance_id])
        message = _("Instance %s has been scheduled for reboot.") % \
                  instance_id
        status = "success"
    except:
        message = _("There were issues trying to reboot instance %s.  "
                  "Please try again.") % instance_id
        status = "error"
    reservations = conn.get_all_instances()
    instances = _reservations_to_instances(reservations)
    return render_to_response('django_nova_syspanel/instances/index.html',
                             {'instances': instances,
                              'message': message,
                              'status': status, },
                             context_instance=template.RequestContext(request))
