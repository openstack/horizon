# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

import collections
import copy
import logging
import os
import socket
import time
import unittest

from django.conf import settings
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.storage import default_storage
from django.contrib.sessions.backends.base import SessionBase
from django.core.handlers import wsgi
from django import http
from django import test as django_test
from django.test.client import RequestFactory
from django.test import tag
from django.test import utils as django_test_utils
from django.utils.encoding import force_text
import six

from django.contrib.staticfiles.testing \
    import StaticLiveServerTestCase as LiveServerTestCase

from horizon import middleware

# Python 3.8 removes the ability to import the abstract base classes from
# 'collections', but 'collections.abc' is not present in Python 2.7
# TODO(stephenfin): Remove when we drop support for Python 2.7
# pylint: disable=ungrouped-imports
if hasattr(collections, 'abc'):
    from collections.abc import Mapping
else:
    from collections import Mapping


LOG = logging.getLogger(__name__)


# NOTE: Several distributions can't ship Selenium, or the Firefox
# component of it, due to its non-free license. So they have to patch
# it out of test-requirements.txt Avoid import failure and force not
# running selenium tests if we attempt to run selenium tests using the
# Firefox driver and it is not available.
try:
    from selenium.webdriver.support import ui as selenium_ui
    import xvfbwrapper  # Only needed when running the Selenium tests headless

    from horizon.test.webdriver import WebDriver
except ImportError as e:
    LOG.warning("%s, force WITH_SELENIUM=False", e)
    os.environ['WITH_SELENIUM'] = ''

# Makes output of failing tests much easier to read.
wsgi.WSGIRequest.__repr__ = lambda self: "<class 'django.http.HttpRequest'>"


class SessionStore(SessionBase):
    """Dict like object for simulating sessions in unittests."""

    def load(self):
        self.create()
        return {}

    def create(self):
        self.modified = True

    def save(self, must_create=False):
        self._session_key = self._get_session_key()
        self.modified = True

    def exists(self, session_key=None):
        return False

    def delete(self, session_key=None):

        self._session_key = ''
        self._session_cache = {}
        self.modified = True

    def cycle_key(self):
        self.save()

    @classmethod
    def clear_expired(cls):
        pass


class RequestFactoryWithMessages(RequestFactory):
    def get(self, *args, **kwargs):
        req = super(RequestFactoryWithMessages, self).get(*args, **kwargs)
        req.user = User()
        req.session = SessionStore()
        req._messages = default_storage(req)
        return req

    def post(self, *args, **kwargs):
        req = super(RequestFactoryWithMessages, self).post(*args, **kwargs)
        req.user = User()
        req.session = SessionStore()
        req._messages = default_storage(req)
        return req


@unittest.skipIf(os.environ.get('SKIP_UNITTESTS', False),
                 "The SKIP_UNITTESTS env variable is set.")
class TestCase(django_test.TestCase):
    """Base test case class for Horizon with numerous additional features.

      * A ``RequestFactory`` class which supports Django's ``contrib.messages``
        framework via ``self.factory``.
      * A ready-to-go request object via ``self.request``.
    """

    def setUp(self):
        super(TestCase, self).setUp()
        self._setup_test_data()
        self._setup_factory()
        self._setup_user()
        self._setup_request()
        # A dummy get_response function (which is not callable) is passed
        # because middlewares below are used only to populate request attrs.
        middleware.HorizonMiddleware('dummy_get_response') \
            ._process_request(self.request)
        AuthenticationMiddleware('dummy_get_response') \
            .process_request(self.request)
        os.environ["HORIZON_TEST_RUN"] = "True"

    def _setup_test_data(self):
        pass

    def _setup_factory(self):
        self.factory = RequestFactoryWithMessages()

    def _setup_user(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.assertTrue(self.client.login(username="test", password="test"))

    def _setup_request(self):
        self.request = http.HttpRequest()
        self.request.session = self.client.session

    def tearDown(self):
        super(TestCase, self).tearDown()
        del os.environ["HORIZON_TEST_RUN"]

    def set_permissions(self, permissions=None):
        perm_ids = Permission.objects.values_list('id', flat=True)
        self.user.user_permissions.remove(*perm_ids)
        for name in permissions:
            ct, create = ContentType.objects.get_or_create(model=name,
                                                           app_label='horizon')
            perm, create = Permission.objects.get_or_create(codename=name,
                                                            content_type=ct,
                                                            name=name)
            self.user.user_permissions.add(perm)
        if hasattr(self.user, "_perm_cache"):
            del self.user._perm_cache

    if six.PY3:
        # Python 2 assert methods renamed in Python 3
        def assertItemsEqual(self, expected_seq, actual_seq, msg=None):
            self.assertCountEqual(expected_seq, actual_seq, msg)

        def assertNotRegexpMatches(self, text, unexpected_regexp, msg=None):
            self.assertNotRegex(text, unexpected_regexp, msg)

    def assertNoMessages(self, response=None):
        """Asserts no messages have been attached by the messages framework.

        The expected messages framework is ``django.contrib.messages``.
        """
        self.assertMessageCount(response, success=0, warn=0, info=0, error=0)

    def assertMessageCount(self, response=None, **kwargs):
        """Asserts that the expected number of messages have been attached.

        The expected number of messages can be specified per message type.
        Usage would look like ``self.assertMessageCount(success=1)``.
        """
        temp_req = self.client.request(**{'wsgi.input': None})
        temp_req.COOKIES = self.client.cookies
        storage = default_storage(temp_req)
        messages = []

        if response is None:
            # To gain early access to the messages we have to decode the
            # cookie on the test client.
            if 'messages' in self.client.cookies:
                message_cookie = self.client.cookies['messages'].value
                messages = storage._decode(message_cookie)
        # Check for messages in the context
        elif hasattr(response, "context") and "messages" in response.context:
            messages = response.context["messages"]
        # Check for messages attached to the request on a TemplateResponse
        elif hasattr(response, "_request") and hasattr(response._request,
                                                       "_messages"):
            messages = response._request._messages._queued_messages

        # If we don't have messages and we don't expect messages, we're done.
        if not any(kwargs.values()) and not messages:
            return

        # If we expected messages and have none, that's a problem.
        if any(kwargs.values()) and not messages:
            error_msg = "Messages were expected, but none were set."
            assert 0 == sum(kwargs.values()), error_msg

        # Otherwise, make sure we got the expected messages.
        for msg_type, count in kwargs.items():
            msgs = [force_text(m.message)
                    for m in messages if msg_type in m.tags]
            assert len(msgs) == count, \
                "%s messages not as expected: %s" % (msg_type.title(),
                                                     ", ".join(msgs))


@tag('selenium')
class SeleniumTestCase(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        socket.setdefaulttimeout(60)
        if os.environ.get('WITH_SELENIUM', False):
            time.sleep(1)
            # Start a virtual display server for running the tests headless.
            if os.environ.get('SELENIUM_HEADLESS', False):
                cls.vdisplay = xvfbwrapper.Xvfb(width=1280, height=720)
                cls.vdisplay.start()
            cls.selenium = WebDriver()
        super(SeleniumTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        if os.environ.get('WITH_SELENIUM', False):
            cls.selenium.quit()
            time.sleep(1)
        if hasattr(cls, 'vdisplay'):
            cls.vdisplay.stop()
        super(SeleniumTestCase, cls).tearDownClass()

    def setUp(self):
        socket.setdefaulttimeout(60)
        self.selenium.implicitly_wait(30)
        self.ui = selenium_ui
        super(SeleniumTestCase, self).setUp()


class JasmineTests(SeleniumTestCase):
    """Helper class which allows you to create a simple Jasmine test.

    Jasmine tests are run through Selenium.
    To run a jasmine test suite, create a class which extends JasmineTests in
    the :file:`horizon/test/jasmine/jasmine_tests.py` and define two class
    attributes

    .. attribute:: sources

        A list of JS source files (the {{ STATIC_URL }} will be added
        automatically, these are the source files tested

    .. attribute:: specs

        A list of Jasmine JS spec files (the {{ STATIC_URL }} will be added
        automatically

    .. attribute:: template_name

        A template which will contain the html needed by the test,
        this attribute is optional, if it is not specified the default template
        will be used. The template, if specified, must extends
        :file:`horizon/jasmine/jasmine.html` and inserts the html in a block
        whose name must be content
    """
    sources = []
    specs = []
    template_name = None

    def run_jasmine(self):
        self.selenium.get(
            "%s%s%s" % (self.live_server_url,
                        "/jasmine/",
                        self.__class__.__name__))

        wait = self.ui.WebDriverWait(self.selenium, 120)

        def jasmine_done(driver):
            text = driver.find_element_by_class_name("duration").text
            return "finished" in text

        wait.until(jasmine_done)
        failures = \
            self.selenium.find_elements_by_css_selector(".spec-detail.failed")

        results = []
        for failure in failures:
            results.append(
                failure.find_element_by_class_name("description").text)
            results.append(
                failure.find_element_by_class_name("stack-trace").text)

        self.assertEqual(results, [], '\n\n' + '\n\n'.join(results) + '\n\n')

    def test(self):
        if self.__class__ == JasmineTests:
            return
        self.run_jasmine()


class update_settings(django_test_utils.override_settings):
    """override_settings which allows override an item in dict.

    django original override_settings replaces a dict completely,
    however OpenStack dashboard setting has many dictionary configuration
    and there are test case where we want to override only one item in
    a dictionary and keep other items in the dictionary.
    This version of override_settings allows this if keep_dict is True.

    If keep_dict False is specified, the original behavior of
    Django override_settings is used.
    """

    def __init__(self, keep_dict=True, **kwargs):
        if keep_dict:
            for key, new_value in kwargs.items():
                value = getattr(settings, key, None)
                if (isinstance(new_value, Mapping) and
                        isinstance(value, Mapping)):
                    copied = copy.copy(value)
                    copied.update(new_value)
                    kwargs[key] = copied
        super(update_settings, self).__init__(**kwargs)


class IsA(object):
    """Class to compare param is a specified class."""
    def __init__(self, cls):
        self.cls = cls

    def __eq__(self, other):
        return isinstance(other, self.cls)


class IsHttpRequest(IsA):
    """Class to compare param is django.http.HttpRequest."""
    def __init__(self):
        super(IsHttpRequest, self).__init__(http.HttpRequest)
