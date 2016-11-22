# Copyright 2012 Nebula, Inc.
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

from cinderclient import exceptions as cinder_exceptions
import glanceclient.exc as glance_exceptions
import heatclient.exc as heat_exceptions
from keystoneclient import exceptions as keystone_exceptions
from neutronclient.common import exceptions as neutron_exceptions
from novaclient import exceptions as nova_exceptions
import six
from swiftclient import client as swift_exceptions

from openstack_dashboard.test.test_data import utils


def create_stubbed_exception(cls, status_code=500):
    msg = "Expected failure."

    def fake_init_exception(self, code=None, message=None, **kwargs):
        if code is not None:
            if hasattr(self, 'http_status'):
                self.http_status = code
            else:
                self.code = code
        self.message = message or self.__class__.message

        try:
            # Neutron sometimes updates the message with additional
            # information, like a reason.
            self.message = self.message % kwargs
        except Exception:
            pass  # We still have the main error message.

    def fake_str(self):
        return str(self.message)

    def fake_unicode(self):
        return six.text_type(self.message)

    cls.__init__ = fake_init_exception
    cls.__str__ = fake_str
    cls.__unicode__ = fake_unicode
    cls.silence_logging = True
    return cls(status_code, msg)


def data(TEST):
    TEST.exceptions = utils.TestDataContainer()

    unauth = keystone_exceptions.Unauthorized
    TEST.exceptions.keystone_unauthorized = create_stubbed_exception(unauth)

    keystone_exception = keystone_exceptions.ClientException
    TEST.exceptions.keystone = create_stubbed_exception(keystone_exception)

    nova_exception = nova_exceptions.ClientException
    TEST.exceptions.nova = create_stubbed_exception(nova_exception)

    nova_unauth = nova_exceptions.Unauthorized
    TEST.exceptions.nova_unauthorized = create_stubbed_exception(nova_unauth)

    glance_exception = glance_exceptions.ClientException
    TEST.exceptions.glance = create_stubbed_exception(glance_exception)

    neutron_exception = neutron_exceptions.NeutronClientException
    TEST.exceptions.neutron = create_stubbed_exception(neutron_exception)

    swift_exception = swift_exceptions.ClientException
    TEST.exceptions.swift = create_stubbed_exception(swift_exception)

    cinder_exception = cinder_exceptions.BadRequest
    TEST.exceptions.cinder = create_stubbed_exception(cinder_exception)

    heat_exception = heat_exceptions.HTTPException
    TEST.exceptions.heat = create_stubbed_exception(heat_exception)
