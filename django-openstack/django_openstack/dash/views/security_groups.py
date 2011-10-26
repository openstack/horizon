# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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
Views for managing Nova instances.
"""
import logging

from django import http
from django import template
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import validators
from django import shortcuts
from django.shortcuts import redirect, render_to_response
from django.utils.translation import ugettext as _

from django_openstack import api
from django_openstack import forms
from novaclient import exceptions as novaclient_exceptions


LOG = logging.getLogger('django_openstack.dash.views.security_groups')


class CreateGroup(forms.SelfHandlingForm):
    name = forms.CharField(validators=[validators.validate_slug])
    description = forms.CharField()
    tenant_id = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            LOG.info('Add security_group: "%s"' % data)

            security_group = api.security_group_create(request,
                                                       data['name'],
                                                       data['description'])
            messages.info(request, _('Successfully created security_group: %s')
                                    % data['name'])
            return shortcuts.redirect('dash_security_groups',
                                       data['tenant_id'])
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in CreateGroup")
            messages.error(request, _('Error creating security group: %s') %
                                     e.message)


class DeleteGroup(forms.SelfHandlingForm):
    tenant_id = forms.CharField(widget=forms.HiddenInput())
    security_group_id = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            LOG.info('Delete security_group: "%s"' % data)

            security_group = api.security_group_delete(request,
                                                     data['security_group_id'])
            messages.info(request, _('Successfully deleted security_group: %s')
                                    % data['security_group_id'])
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in DeleteGroup")
            messages.error(request, _('Error deleting security group: %s')
                                     % e.message)
        return shortcuts.redirect('dash_security_groups', data['tenant_id'])


class AddRule(forms.SelfHandlingForm):
    ip_protocol = forms.ChoiceField(choices=[('tcp', 'tcp'),
                                             ('udp', 'udp'),
                                             ('icmp', 'icmp')])
    from_port = forms.CharField()
    to_port = forms.CharField()
    cidr = forms.CharField()
    # TODO (anthony) source group support
    # group_id = forms.CharField()

    security_group_id = forms.CharField(widget=forms.HiddenInput())
    tenant_id = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        tenant_id = data['tenant_id']
        try:
            LOG.info('Add security_group_rule: "%s"' % data)

            rule = api.security_group_rule_create(request,
                                                  data['security_group_id'],
                                                  data['ip_protocol'],
                                                  data['from_port'],
                                                  data['to_port'],
                                                  data['cidr'])
            messages.info(request, _('Successfully added rule: %s') \
                                    % rule.id)
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in AddRule")
            messages.error(request, _('Error adding rule security group: %s')
                                     % e.message)
        return shortcuts.redirect(request.build_absolute_uri())


class DeleteRule(forms.SelfHandlingForm):
    security_group_rule_id = forms.CharField(widget=forms.HiddenInput())
    tenant_id = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        security_group_rule_id = data['security_group_rule_id']
        tenant_id = data['tenant_id']
        try:
            LOG.info('Delete security_group_rule: "%s"' % data)

            security_group = api.security_group_rule_delete(
                                                request,
                                                security_group_rule_id)
            messages.info(request, _('Successfully deleted rule: %s')
                                    % security_group_rule_id)
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in DeleteRule")
            messages.error(request, _('Error authorizing security group: %s')
                                     % e.message)
        return shortcuts.redirect(request.build_absolute_uri())


@login_required
def index(request, tenant_id):
    delete_form, handled = DeleteGroup.maybe_handle(request,
                                initial={'tenant_id': tenant_id})

    if handled:
        return handled

    try:
        security_groups = api.security_group_list(request)
    except novaclient_exceptions.ClientException, e:
        security_groups = []
        LOG.exception("ClientException in security_groups index")
        messages.error(request, _('Error fetching security_groups: %s')
                                 % e.message)

    return shortcuts.render_to_response(
    'django_openstack/dash/security_groups/index.html', {
        'security_groups': security_groups,
        'delete_form': delete_form,
    }, context_instance=template.RequestContext(request))


@login_required
def edit_rules(request, tenant_id, security_group_id):
    add_form, handled = AddRule.maybe_handle(request,
                           initial={'tenant_id': tenant_id,
                                      'security_group_id': security_group_id})
    if handled:
        return handled

    delete_form, handled = DeleteRule.maybe_handle(request,
                              initial={'tenant_id': tenant_id,
                                       'security_group_id': security_group_id})
    if handled:
        return handled

    try:
        security_group = api.security_group_get(request, security_group_id)
    except novaclient_exceptions.ClientException, e:
        LOG.exception("ClientException in security_groups rules edit")
        messages.error(request, _('Error getting security_group: %s')
                                  % e.message)
        return shortcuts.redirect('dash_security_groups', tenant_id)

    return shortcuts.render_to_response(
        'django_openstack/dash/security_groups/edit_rules.html', {
        'security_group': security_group,
        'delete_form': delete_form,
        'form': add_form,
    }, context_instance=template.RequestContext(request))


@login_required
def create(request, tenant_id):
    form, handled = CreateGroup.maybe_handle(request,
                                initial={'tenant_id': tenant_id})
    if handled:
        return handled

    return shortcuts.render_to_response(
    'django_openstack/dash/security_groups/create.html', {
        'form': form,
    }, context_instance=template.RequestContext(request))
