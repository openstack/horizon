from django.conf import settings

import glance.client
import httplib
import json
import openstack.compute
import openstackx.admin
import openstackx.extras
import openstackx.auth
from urlparse import urlparse

# FIXME this is duplicated in syspanel need to consolidate


def compute_api(request):
    compute = openstack.compute.Compute(auth_token=request.session['token'],
                                        management_url=settings.OPENSTACK_MANAGER_URL)
    compute.client.auth_token = auth_token=request.session['token']
    compute.client.management_url = settings.OPENSTACK_MANAGER_URL
    return compute


def account_api(request):
    return openstackx.extras.Account(auth_token=request.session['token'],
                                    management_url=settings.OPENSTACK_ACCOUNT_URL)


def glance_api(request):
    o = urlparse(settings.OPENSTACK_GLANCE_URL)
    return glance.client.Client(o.hostname, o.port)


def admin_api(request):
    return openstackx.admin.Admin(auth_token=request.session['token'],
                                 management_url=settings.OPENSTACK_ADMIN_MANAGER_URL)


def extras_api(request):
    return openstackx.extras.Extras(auth_token=request.session['token'],
                                   management_url=settings.OPENSTACK_ADMIN_MANAGER_URL)


def auth_api():
    return  openstackx.auth.Auth(management_url=\
                                settings.OPENSTACK_KEYSTONE_URL)


def token_info(token):
    hdrs = {"Content-type": "application/json",
            "X_AUTH_TOKEN": settings.OPENSTACK_ADMIN_TOKEN,
            "Accept": "text/json"}
    o = urlparse(settings.OPENSTACK_ACCOUNT_URL)
    conn = httplib.HTTPConnection(o.hostname, o.port)
    conn.request("GET", "/v2.0/tokens/%s" % token, headers=hdrs)
    response = conn.getresponse()
    data = json.loads(response.read())

    admin = False
    for role in data['auth']['user']['roleRefs']:
        if role['roleId'] == 'Admin':
            admin = True

    return {'tenant': data['auth']['user']['tenantId'],
            'user': data['auth']['user']['username'],
            'admin': admin}
