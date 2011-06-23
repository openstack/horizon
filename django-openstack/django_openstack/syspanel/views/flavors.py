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


class CreateFlavor(forms.SelfHandlingForm):
    flavorid = forms.CharField(max_length="10", label="Flavor ID")
    name = forms.CharField(max_length="5", label="Name")
    vcpus = forms.CharField(max_length="5", label="VCPUs")
    memory_mb = forms.CharField(max_length="5", label="Memory MB")
    disk_gb = forms.CharField(max_length="5", label="Disk GB")

    def handle(self, request, data):
        api.flavor_create(request,
                          data['name'],
                          int(data['memory_mb']),
                          int(data['vcpus']),
                          int(data['disk_gb']),
                          int(data['flavorid']))
        messages.success(request,
                '%s was successfully added to flavors.' % data['name'])
        return redirect('syspanel_flavors')


class DeleteFlavor(forms.SelfHandlingForm):
    flavorid = forms.CharField(required=True)

    def handle(self, request, data):
        try:
            flavor_id = data['flavorid']
            flavor = api.flavor_get(request, flavor_id)
            api.flavor_delete(request, flavor_id, True)
            messages.info(request, 'Successfully deleted flavor: %s' %
                          flavor.name)
        except api_exceptions.ApiException, e:
            messages.error(request, 'Unable to delete flavor: %s' %
                                     e.message)
        return redirect(request.build_absolute_uri())

@login_required
def index(request):
    for f in (DeleteFlavor,):
        _, handled = f.maybe_handle(request)
        if handled:
            return handled

    delete_form = DeleteFlavor()

    flavors = []
    try:
        flavors = api.flavor_list_admin(request)
    except api_exceptions.ApiException, e:
        messages.error(request, 'Unable to get usage info: %s' % e.message)

    flavors.sort(key=lambda x: x.id, reverse=True)
    return render_to_response('syspanel_flavors.html',{
        'delete_form': delete_form,
        'flavors': flavors,
    }, context_instance = template.RequestContext(request))


@login_required
def create(request):
    form, handled = CreateFlavor.maybe_handle(request)
    if handled:
        return handled

    return render_to_response('syspanel_create_flavor.html',{
        'form': form,
    }, context_instance = template.RequestContext(request))
