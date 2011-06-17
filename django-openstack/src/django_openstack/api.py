from django.conf import settings

import logging

import glance.client
import httplib
import json
import openstack.compute
import openstackx.admin
import openstackx.extras
import openstackx.auth
from urlparse import urlparse
import json

def url_for(request, service_name, admin=False):
    catalog = request.session['serviceCatalog']
    if admin:
        rv  = catalog[service_name][0]['adminURL']
    else:
        rv = catalog[service_name][0]['internalURL']
    return rv

def compute_api(request):
    compute =  openstack.compute.Compute(auth_token=request.session['token'],
                                         management_url=url_for(request, 'nova'))
    # this below hack is necessary to make the jacobian compute client work
    compute.client.auth_token = request.session['token']
    compute.client.management_url = url_for(request, 'nova')
    return compute

def account_api(request):
    return openstackx.extras.Account(auth_token=request.session['token'],
                                    management_url=url_for(request, 'keystone', True))

def glance_api(request):
    o = urlparse(url_for(request, 'glance'))
    return glance.client.Client(o.hostname, o.port)

def admin_api(request):
    return openstackx.admin.Admin(auth_token=request.session['token'],
                                 management_url=url_for(request, 'nova', True))

def extras_api(request):
    return openstackx.extras.Extras(auth_token=request.session['token'],
                                   management_url=url_for(request, 'nova'))


def auth_api():
    return openstackx.auth.Auth(management_url=\
                               settings.OPENSTACK_KEYSTONE_URL)


def get_tenant(request, tenant_id):
  tenants = auth_api().tenants.for_token(request.session['token'])
  for t in tenants:
      if str(t.id) == str(tenant_id):
          return t



def token_info(token):
    hdrs = {"Content-type": "application/json",
            "X_AUTH_TOKEN": settings.OPENSTACK_ADMIN_TOKEN,
            "Accept": "text/json"}

    o = urlparse(token.serviceCatalog['keystone'][0]['adminURL'])
    conn = httplib.HTTPConnection(o.hostname, o.port)
    conn.request("GET", "/v2.0/tokens/%s" % token.id, headers=hdrs)
    response = conn.getresponse()
    data = json.loads(response.read())

    admin = False
    for role in data['auth']['user']['roleRefs']:
        if role['roleId'] == 'Admin':
            admin = True

    return {'tenant': data['auth']['user']['tenantId'],
            'user': data['auth']['user']['username'],
            'admin': admin}
