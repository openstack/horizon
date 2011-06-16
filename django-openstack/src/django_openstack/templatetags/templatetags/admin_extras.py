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
Template tags for extending the Django admin interface.
"""

from django.contrib.admin.templatetags.admin_list import (items_for_result,
                                                          result_headers)
from django.core.urlresolvers import reverse
from django.template import Library
from django.utils.safestring import mark_safe


register = Library()


def project_result_list(cl):
    headers = list(result_headers(cl))
    headers.append({'text': mark_safe('&nbsp;')})

    results = list()

    for project in cl.result_list:
        rl = list(items_for_result(cl, project, None))

        url = reverse('admin_project_sendcredentials',
                      args=[project.projectname])
        content = mark_safe('<td><a href="%s">Send Credentials</a></td>' % url)

        rl.append(content)
        results.append(rl)

    return {
        'cl': cl,
        'result_headers': headers,
        'results': results
    }
project_result_list = register.inclusion_tag('admin/change_list_results.html')(project_result_list)
