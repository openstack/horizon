from django import http
from django import template
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render_to_response
from django_nova_syspanel.models import get_nova_admin_connection


@login_required
def index(request):
    nova = get_nova_admin_connection()
    vpns = nova.get_vpns()
    return render_to_response('django_nova_syspanel/vpns/index.html',
                             {'vpns': vpns, },
                             context_instance=template.RequestContext(request))


@login_required
def console(request, project_id):
    nova = get_nova_admin_connection()
    conn = nova.connection_for(settings.NOVA_ADMIN_USER, project_id)
    vpn = [x for x in nova.get_vpns() if x.project_id == project_id][0]
    console = conn.get_console_output(vpn.instance_id)
    response = http.HttpResponse(mimetype='text/plain')
    response.write(console.output)
    response.flush()
    return response


@login_required
def restart(request, project_id):
    nova = get_nova_admin_connection()
    conn = nova.connection_for(settings.NOVA_ADMIN_USER, project_id)
    vpn = [x for x in nova.get_vpns() if x.project_id == project_id][0]
    conn.reboot_instances([vpn.instance_id])
    return redirect('django_nova_syspanel/vpns')


@login_required
def terminate(request, project_id):
    nova = get_nova_admin_connection()
    conn = nova.connection_for(settings.NOVA_ADMIN_USER, project_id)
    vpn = [x for x in nova.get_vpns() if x.project_id == project_id][0]
    conn.terminate_instances([vpn.instance_id])
    return redirect('django_nova_syspanel/vpns')


@login_required
def launch(request, project_id):
    nova = get_nova_admin_connection()
    nova.start_vpn(project_id)
    return redirect('django_nova_syspanel/vpns')


@login_required
def send_credentials(request, project_id, user_id):
    # TODO we need to pass a user id as well
    nova = get_nova_admin_connection()
    nova.get_zip(user_id, project_id)
    return redirect('django_nova_syspanel/vpns')
