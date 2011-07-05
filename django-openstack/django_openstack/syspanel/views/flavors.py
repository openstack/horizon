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
    name = forms.CharField(max_length="25", label="Name")
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
            api.flavor_delete(request, flavor_id, False)
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

    service_list = []
    usage_list = []
    max_vcpus = max_gigabytes = 0
    total_ram = 0

    try:
        service_list = api.service_list(request)
    except api_exceptions.ApiException, e:
        messages.error(request, 'Unable to get service info: %s' % e.message)

    for service in service_list:
        if service.type == 'nova-compute':
            max_vcpus += service.stats['max_vcpus']
            max_gigabytes += service.stats['max_gigabytes']
            total_ram += settings.COMPUTE_HOST_RAM_GB

    global_summary = {'max_vcpus': max_vcpus, 'max_gigabytes': max_gigabytes,
                      'total_active_disk_size': 0, 'total_active_vcpus': 0,
                      'total_active_ram_size': 0}

    for usage in usage_list:
        usage = usage.to_dict()
        for k in usage:
            v = usage[k]
            if type(v) in [float, int]:
                if not k in global_summary:
                    global_summary[k] = 0
                global_summary[k] += v

    max_disk_tb = used_disk_tb = available_disk_tb = 0

    max_disk_tb = global_summary['max_gigabytes'] / float(1000)
    used_disk_tb = global_summary['total_active_disk_size'] / float(1000)
    available_disk_tb = (global_summary['max_gigabytes'] / float(1000) - \
                        global_summary['total_active_disk_size'] / float(1000))
    used_ram = global_summary['total_active_ram_size'] / float(1024)
    avail_ram = total_ram - used_ram

    ram_unit = "GB"
    if total_ram > 999:
        ram_unit = "TB"
        total_ram /= float(1024)
        used_ram /= float(1024)
        avail_ram /= float(1024)

    return render_to_response('syspanel_create_flavor.html',{
        'available_cores': global_summary['max_vcpus'] - global_summary['total_active_vcpus'],
        'available_disk_tb': available_disk_tb,
        'avail_ram': avail_ram,
        'ram_unit': ram_unit,
        'form': form,
    }, context_instance = template.RequestContext(request))
