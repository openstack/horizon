from django import template
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response


@login_required
def index(request):
    return render_to_response('django_nova_syspanel/index.html',
                             {},
                             context_instance=template.RequestContext(request))
