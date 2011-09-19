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

''' Test for django mailer.

This test is pretty much worthless, and should be removed once real testing of
views that send emails is implemented
'''

from django import test
from django.core import mail
from mailer import engine
from mailer import send_mail


class DjangoMailerPresenceTest(test.TestCase):
    def test_mailsent(self):
        send_mail('subject', 'message_body', 'from@test.com', ['to@test.com'])
        engine.send_all()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'subject')
