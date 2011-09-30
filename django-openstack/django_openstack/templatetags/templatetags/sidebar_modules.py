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

from django import template
from django_openstack import signals

register = template.Library()


@register.inclusion_tag('django_openstack/common/_sidebar_module.html')
def dash_sidebar_modules(request):
    signals_call = signals.dash_modules_detect()
    if signals_call:
        return {'modules': [module[1] for module in signals_call
                                    if module[1]['type'] == "dash"],
                    'request': request}
    else:
        return {}


@register.inclusion_tag('django_openstack/common/_sidebar_module.html')
def syspanel_sidebar_modules(request):
    signals_call = signals.dash_modules_detect()
    if signals_call:
        return {'modules': [module[1] for module in signals_call
                                if module[1]['type'] == "syspanel"],
                    'request': request}
    else:
        return {}
