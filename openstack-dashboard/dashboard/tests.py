# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
