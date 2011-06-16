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
Management commands for synchronizing the Django auth database and Nova
users database.
"""

from django.core.management.base import NoArgsCommand
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from django_nova.connection import get_nova_admin_connection


class Command(NoArgsCommand):
    help = _('Creates nova users for all users in the django auth database.')

    def handle_noargs(self, **options):
        nova = get_nova_admin_connection()
        users = User.objects.all()
        for user in users:
            if not nova.has_user(user.username):
                self.stdout.write(_('creating user %s... ') % user.username)
                nova.create_user(user.username)
                self.stdout.write('ok\n')
