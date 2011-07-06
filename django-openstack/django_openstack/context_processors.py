from django_openstack import api
from django.contrib import messages
from openstackx.api import exceptions as api_exceptions


def tenants(request):
    if not request.user or not request.user.is_authenticated():
        return {}

    try:
        return {'tenants': api.token_list_tenants(request, request.user.token)}
    except api_exceptions.ApiException, e:
        messages.error(request, "Unable to retrieve tenant list from\
                                  keystone: %s" % e.message)
        return {'tenants': []}
