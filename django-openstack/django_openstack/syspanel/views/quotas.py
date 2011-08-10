# vim: tabstop=4 shiftwidth=4 softtabstop=4

from operator import itemgetter

from django import template
from django import http
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.shortcuts import render_to_response
from openstackx.api import exceptions as api_exceptions


from django_openstack import api
from django_openstack import forms
from django_openstack.decorators import enforce_admin_access

@login_required
@enforce_admin_access
def index(request):
    quotas = api.admin_api(request).quota_sets.get(True)._info
    quotas['ram'] = int(quotas['ram']) / 100
    quotas.pop('id')

    return render_to_response('syspanel_quotas.html',{
        'quotas': quotas,
    }, context_instance = template.RequestContext(request))

