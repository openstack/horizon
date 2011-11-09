from django import test
from noseselenium.cases import SeleniumTestCaseMixin


class SeleniumTests(test.TestCase, SeleniumTestCaseMixin):
    def test_splash(self):
        self.selenium.open("/")
        self.failUnless(self.selenium.is_text_present("User Name"))

    def test_qunit(self):
        self.selenium.open("/qunit/")
        self.selenium.wait_for_page_to_load("2000")
        self.failUnless(self.selenium.is_text_present("0 failed"))
