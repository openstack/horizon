# vim: tabstop=4 shiftwidth=4 softtabstop=4

from django import shortcuts
from django.contrib import messages

from django_openstack import api
from django_openstack.nova import forms as nova_forms
from openstackx.api import exceptions as api_exceptions


def login(request):
    if request.method == 'POST':
        form = nova_forms.Login(request.POST)
        if form.is_valid():
            try:
                userdata = form.clean()
                token = api.auth_api().tokens.create(userdata['tenant'],
                                                     userdata['username'],
                                                     userdata['password'])
                info = api.token_info(token.id)
                request.session['token'] = token.id
                request.session['user'] = info['user']
                request.session['tenant'] = info['tenant']
                request.session['admin'] = info['admin']

                if request.session['admin']:
                    return shortcuts.redirect('admin_overview')
                else:
                    return shortcuts.redirect('user_overview')

            except api_exceptions.Unauthorized as e:
                messages.error(request, 'Error authenticating: %s' % e.message)
    return shortcuts.redirect('index')


def switch_tenants(request, tenant_id):
    if request.method == 'POST':
        form = nova_forms.LoginWithoutTenant(request.POST)
        if form.is_valid():
            try:
                userdata = form.clean()
                token = api.auth_api().tokens.create(tenant_id,
                                                     userdata['username'],
                                                     userdata['password'])
                request.session['token'] = token.id
                request.session['user'] = userdata['username']
                request.session['tenant'] = tenant_id
                messages.error(request, token)
                return shortcuts.redirect('novaO_overview')

            except api_exceptions.Unauthorized as ex:
                messages.error(request, 'Error authenticating:')
                return shortcuts.redirect('novaO_overview')

    else:
        form = nova_forms.LoginWithoutTenant()

        return render_to_response('switch_tenants.html', {
            'form': form,
            'tenant_id': tenant_id,
        },context_instance=template.RequestContext(request))


def logout(request):
    request.session.clear()
    return shortcuts.redirect('novaO_instances')



