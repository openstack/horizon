from django import template
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response

from django_nova_syspanel.models import get_nova_admin_connection


@login_required
def index(request):
    nova = get_nova_admin_connection()
    nodes = nova.get_hosts()
    return render_to_response('django_nova_syspanel/cloudview/index.html',
                             {'nodes': nodes, },
                             context_instance=template.RequestContext(request))
