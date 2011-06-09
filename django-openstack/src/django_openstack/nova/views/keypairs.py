# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Views for managing Nova keypairs.
"""

from django import http
from django import template
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render_to_response
from django.utils.translation import ugettext as _
from django_openstack import log as logging
from django_openstack.nova import exceptions
from django_openstack.nova import forms
from django_openstack.nova import shortcuts
from django_openstack.nova.exceptions import handle_nova_error


LOG = logging.getLogger('django_openstack.nova')


@login_required
@handle_nova_error
def index(request, project_id, download_key=None):
    project = shortcuts.get_project_or_404(request, project_id)
    keypairs = project.get_key_pairs()

    return render_to_response('django_openstack/nova/keypairs/index.html', {
        'create_form': forms.CreateKeyPairForm(project),
        'region': project.region,
        'project': project,
        'keypairs': keypairs,
        'download_key': download_key
    }, context_instance=template.RequestContext(request))


@login_required
@handle_nova_error
def add(request, project_id):
    project = shortcuts.get_project_or_404(request, project_id)

    if request.method == 'POST':
        form = forms.CreateKeyPairForm(project, request.POST)

        if form.is_valid():
            try:
                keypair = project.create_key_pair(form.cleaned_data['name'])
            except exceptions.NovaApiError, e:
                messages.error(request,
                               _('Unable to create key: %s') % e.message)
                LOG.error('Unable to create key for user "%s" on project "%s".'
                          ' Exception: "%s"' %
                          (str(request.user), project_id, e.message))
            else:
                LOG.info('Keypair "%s" for project "%s" created successfully' %
                        (keypair.name, project_id))
                if request.POST['js'] == '1':
                    request.session['key.%s' % keypair.name] = keypair.material
                    return index(request,
                                 project_id,
                                 download_key=keypair.name)
                else:
                    response = http.HttpResponse(mimetype='application/binary')
                    response['Content-Disposition'] = \
                        'attachment; filename=%s.pem' % \
                        form.cleaned_data['name']
                    response.write(keypair.material)
                    return response
        else:
            keypairs = project.get_key_pairs()

            return render_to_response(
                'django_openstack/nova/keypairs/index.html',
                {'create_form': form,
                 'region': project.region,
                 'project': project,
                 'keypairs': keypairs},
                context_instance=template.RequestContext(request))

    return redirect('nova_keypairs', project_id)


@login_required
@handle_nova_error
def delete(request, project_id):
    project = shortcuts.get_project_or_404(request, project_id)

    if request.method == 'POST':
        key_name = request.POST['key_name']

        try:
            project.delete_key_pair(key_name)
        except exceptions.NovaApiError, e:
            messages.error(request,
                           _('Unable to delete key: %s') % e.message)
            LOG.error('Unable to delete key "%s".  Exception: "%s"' %
                      (key_name, e.message_))
        else:
            messages.success(request,
                             _('Key %s has been successfully deleted.') % \
                             key_name)
            LOG.info('Key "%s" successfully deleted' % key_name)

    return redirect('nova_keypairs', project_id)


@login_required
@handle_nova_error
def download(request, project_id, key_name):
    # Ensure the project exists.
    shortcuts.get_project_or_404(request, project_id)

    try:
        material = request.session.pop('key.%s' % key_name)
    except KeyError:
        return redirect('nova_keypairs', project_id)

    response = http.HttpResponse(mimetype='application/binary')
    response['Content-Disposition'] = 'attachment; filename=%s.pem' % key_name
    response.write(material)

    return response
