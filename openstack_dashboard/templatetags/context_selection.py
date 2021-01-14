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

from django.conf import settings
from django import template


register = template.Library()


def is_multi_region_configured(request):
    return len(request.user.available_services_regions) > 1


# TODO(e0ne): pass OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT to the template
# context and remove `is_multidomain` template tag
def is_multidomain_supported():
    return settings.OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT


@register.simple_tag(takes_context=True)
def is_multi_region(context):
    if 'request' not in context:
        return False
    return is_multi_region_configured(context['request'])


@register.simple_tag
def is_multidomain():
    return is_multidomain_supported()


@register.inclusion_tag('context_selection/_overview.html',
                        takes_context=True)
def show_overview(context):
    if 'request' not in context:
        return {}
    request = context['request']
    project_name = get_project_name(request.user.project_id,
                                    context['authorized_tenants'])

    context = {'domain_supported': is_multidomain_supported(),
               'domain_name': request.user.user_domain_name,
               'project_name': project_name or request.user.project_name,
               'multi_region': is_multi_region_configured(request),
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
    context = {'domain_name': request.user.user_domain_name,
               'request': request}
    return context


@register.inclusion_tag('context_selection/_project_list.html',
                        takes_context=True)
def show_project_list(context):
    max_proj = settings.DROPDOWN_MAX_ITEMS
    if 'request' not in context:
        return {}
    request = context['request']
    projects = sorted(context['authorized_tenants'],
                      key=lambda project: project.name.lower())
    panel = request.horizon.get('panel')
    context = {'projects': projects[:max_proj],
               'project_id': request.user.project_id,
               'page_url': panel.get_absolute_url() if panel else None}
    return context


@register.inclusion_tag('context_selection/_region_list.html',
                        takes_context=True)
def show_region_list(context):
    if 'request' not in context:
        return {}
    request = context['request']
    panel = request.horizon.get('panel')
    context = {'region_name': request.user.services_region,
               'regions': sorted(request.user.available_services_regions,
                                 key=lambda x: (x or '').lower()),
               'page_url': panel.get_absolute_url() if panel else None}
    return context


@register.inclusion_tag('context_selection/_anti_clickjack.html',
                        takes_context=True)
def iframe_embed_settings(context):
    context = {'disallow_iframe_embed': settings.DISALLOW_IFRAME_EMBED}
    return context


def get_project_name(project_id, projects):
    """Retrieves project name for given project id

    Args:
        projects: List of projects
        project_id: project id

    Returns: Project name or None if there is no match
    """
    for project in projects:
        if project_id == project.id:
            return project.name
