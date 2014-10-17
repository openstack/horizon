# Copyright 2014 IBM Corp.
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

from __future__ import absolute_import

from django.conf import settings
from django import template

from openstack_dashboard.api import keystone


register = template.Library()


def is_multidomain_supported():
    return (keystone.VERSIONS.active >= 3 and
            getattr(settings,
                    'OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT',
                    False))


@register.inclusion_tag('context_selection/_overview.html',
                        takes_context=True)
def show_overview(context):
    if 'request' not in context:
        return {}
    request = context['request']
    context = {'domain_supported': is_multidomain_supported(),
               'domain_name': request.user.user_domain_name,
               'project_name': request.user.project_name,
               'multi_region':
               len(request.user.available_services_regions) > 1,
               'region_name': request.user.services_region,
               'request': request}

    return context


@register.inclusion_tag('context_selection/_domain_list.html',
                        takes_context=True)
def show_domain_list(context):
    # TODO(Thai): once domain switching is support, need to revisit
    if 'request' not in context:
        return {}
    request = context['request']
    context = {'domain_supported': is_multidomain_supported(),
               'domain_name': request.user.user_domain_name,
               'request': request}
    return context


@register.inclusion_tag('context_selection/_project_list.html',
                        takes_context=True)
def show_project_list(context):
    max_proj = getattr(settings,
                       'DROPDOWN_MAX_ITEMS',
                       30)
    if 'request' not in context:
        return {}
    request = context['request']
    context = {'projects': sorted(context['authorized_tenants'],
                                  key=lambda project: project.name)[:max_proj],
               'project_id': request.user.project_id,
               'request': request}
    return context


@register.inclusion_tag('context_selection/_region_list.html',
                        takes_context=True)
def show_region_list(context):
    if 'request' not in context:
        return {}
    request = context['request']
    context = {'multi_region':
               len(request.user.available_services_regions) > 1,
               'region_name': request.user.services_region,
               'regions': sorted(request.user.available_services_regions),
               'request': request}
    return context
