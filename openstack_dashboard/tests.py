import os

from django import test
from django.utils import unittest

from selenium.webdriver.firefox.webdriver import WebDriver


@unittest.skipUnless(os.environ.get('WITH_SELENIUM', False),
                     "The WITH_SELENIUM env variable is not set.")
class SeleniumTests(test.LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get('WITH_SELENIUM', False):
            cls.selenium = WebDriver()
        super(SeleniumTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(SeleniumTests, cls).tearDownClass()
        if os.environ.get('WITH_SELENIUM', False):
            cls.selenium.quit()

    def test_splash(self):
        self.selenium.get(self.live_server_url)
        button = self.selenium.find_element_by_tag_name("button")
        self.assertEqual(button.text, "Sign In")

    def test_qunit(self):
        self.selenium.get("%s%s" % (self.live_server_url, "/qunit/")),
        self.selenium.implicitly_wait("1000")
        failed = self.selenium.find_element_by_class_name("failed")
        self.assertEqual(int(failed.text), 0)
