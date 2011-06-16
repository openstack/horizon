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
Database models for authorization credentials and synchronizing Nova users.
"""

import datetime
import random
import re
import sha
from django.conf import settings
from django.contrib.auth import models as auth_models
from django.contrib.sites import models as site_models
from django.core import mail
from django.db import models
from django.db.models.signals import post_save
from django.template.loader import render_to_string
from django_openstack import log as logging
from django_openstack.core import connection
from django_openstack import utils


LOG = logging.getLogger('django_openstack')


SHA1_RE = re.compile('^[a-f0-9]{40}$')


class CredentialsAuthorization(models.Model):
    username = models.CharField(max_length=128)
    project = models.CharField(max_length=128)
    auth_token = models.CharField(max_length=40)
    auth_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s/%s:%s' % (self.username, self.project, self.auth_token)

    @classmethod
    def get_by_token(cls, token):
        if SHA1_RE.search(token):
            try:
                credentials = cls.objects.get(auth_token=token)
            except cls.DoesNotExist:
                return None
            if not credentials.auth_token_expired():
                return credentials
        return None

    @classmethod
    def authorize(cls, username, project):
        return cls.objects.create(username=username,
                                  project=project,
                                  auth_token=cls.create_auth_token(username))

    @staticmethod
    def create_auth_token(username):
        salt = sha.new(str(random.random())).hexdigest()[:5]
        return sha.new(salt + username).hexdigest()

    def auth_token_expired(self):
        expiration_date = datetime.timedelta(
                days=int(settings.CREDENTIAL_AUTHORIZATION_DAYS))

        return self.auth_date + expiration_date <= utils.utcnow()

    def get_download_url(self):
        return settings.CREDENTIAL_DOWNLOAD_URL + self.auth_token

    def get_zip(self):
        nova = connection.get_nova_admin_connection()
        self.delete()
        return nova.get_zip(self.username, self.project)


def credentials_post_save(sender, instance, created, *args, **kwargs):
    """
    Creates a Nova User when a new Django User is created.
    """
    if created:
        site = site_models.Site.objects.get_current()
        user = auth_models.User.objects.get(username=instance.username)
        context = {
            'user': user,
            'download_url': instance.get_download_url(),
            'dashboard_url': 'http://%s/' % site.domain
        }
        subject = render_to_string('credentials/credentials_email_subject.txt')
        body = render_to_string('credentials/credentials_email.txt', context)

        message = mail.EmailMessage(subject=subject.strip(),
                                    body=body,
                                    to=[user.email])
        message.send(fail_silently=False)
        LOG.info('Credentials sent to user "%s" at "%s"' %
                 (instance.name, user.email))
post_save.connect(credentials_post_save,
                  CredentialsAuthorization,
                  dispatch_uid='django_openstack.CredentialsAuthorization.post_save')


def user_post_save(sender, instance, created, *args, **kwargs):
    """
    Creates a Nova User when a new Django User is created.
    """

    # NOTE(devcamcar): If running unit tests, don't use a real endpoint.
    if settings.NOVA_DEFAULT_ENDPOINT is None:
        return

    if created:
        nova = connection.get_nova_admin_connection()
        if not nova.has_user(instance.username):
            nova.create_user(instance.username)
            LOG.info('User "%s" created in Nova' % instance.username)
post_save.connect(user_post_save,
                  auth_models.User,
                  dispatch_uid='django_openstack.User.post_save')
