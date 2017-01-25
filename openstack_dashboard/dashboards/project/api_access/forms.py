# Copyright 2016 NEC Corporation
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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api
from openstack_dashboard import policy


def get_ec2_credentials(request):
    if not policy.check((("identity", "identity:ec2_list_credentials"),),
                        request):
        return None

    project_id = request.user.project_id
    all_keys = api.keystone.list_ec2_credentials(request,
                                                 request.user.id)
    keys = [x for x in all_keys if x.tenant_id == project_id]
    if not keys:
        return None
    return {'ec2_access_key': keys[0].access,
            'ec2_secret_key': keys[0].secret}


class RecreateCredentials(forms.SelfHandlingForm):

    def handle(self, request, context):
        try:
            credential = get_ec2_credentials(request)
            if credential:
                api.keystone.delete_user_ec2_credentials(
                    request,
                    request.user.id,
                    credential['ec2_access_key'])
        except Exception:
            exceptions.handle(
                request, _('Unable to recreate ec2 credentials. '
                           'Failed to delete ec2 credentials.'))
            return False

        try:
            api.keystone.create_ec2_credentials(
                request,
                request.user.id,
                request.user.project_id)
            message = _('Successfully recreated ec2 credentials.')
            messages.success(request, message)
            return True
        except Exception:
            exceptions.handle(
                request, _('Unable to recreate ec2 credentials. '
                           'Failed to create ec2 credentials.'))
            return False
