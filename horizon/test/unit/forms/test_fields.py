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

from django.core.exceptions import ValidationError
from django import shortcuts

from horizon import forms
from horizon.test import helpers as test


class IPFieldTests(test.TestCase):

    def test_validate_ipv4_cidr(self):
        GOOD_CIDRS = ("192.168.1.1/16",
                      "192.0.0.1/17",
                      "0.0.0.0/16",
                      "10.144.11.107/4",
                      "255.255.255.255/0",
                      "0.1.2.3/16",
                      "0.0.0.0/32",
                      # short form
                      "128.0/16",
                      "128/4")
        BAD_CIDRS = ("255.255.255.256\\",
                     "256.255.255.255$",
                     "1.2.3.4.5/41",
                     "0.0.0.0/99",
                     "127.0.0.1/",
                     "127.0.0.1/33",
                     "127.0.0.1/-1",
                     "127.0.0.1/100",
                     # some valid IPv6 addresses
                     "fe80::204:61ff:254.157.241.86/4",
                     "fe80::204:61ff:254.157.241.86/0",
                     "2001:0DB8::CD30:0:0:0:0/60",
                     "2001:0DB8::CD30:0/90")
        ip = forms.IPField(mask=True, version=forms.IPv4)
        for cidr in GOOD_CIDRS:
            self.assertIsNone(ip.validate(cidr))
        for cidr in BAD_CIDRS:
            self.assertRaises(ValidationError, ip.validate, cidr)

    def test_validate_ipv6_cidr(self):
        GOOD_CIDRS = ("::ffff:0:0/56",
                      "2001:0db8::1428:57ab/17",
                      "FEC0::/10",
                      "fe80::204:61ff:254.157.241.86/4",
                      "fe80::204:61ff:254.157.241.86/0",
                      "2001:0DB8::CD30:0:0:0:0/60",
                      "2001:0DB8::CD30:0/90",
                      "::1/128")
        BAD_CIDRS = ("1111:2222:3333:4444:::/",
                     "::2222:3333:4444:5555:6666:7777:8888:\\",
                     ":1111:2222:3333:4444::6666:1.2.3.4/1000",
                     "1111:2222::4444:5555:6666::8888@",
                     "1111:2222::4444:5555:6666:8888/",
                     "::ffff:0:0/129",
                     "1.2.3.4:1111:2222::5555//22",
                     "fe80::204:61ff:254.157.241.86/200",
                     # some valid IPv4 addresses
                     "10.144.11.107/4",
                     "255.255.255.255/0",
                     "0.1.2.3/16")
        ip = forms.IPField(mask=True, version=forms.IPv6)
        for cidr in GOOD_CIDRS:
            self.assertIsNone(ip.validate(cidr))
        for cidr in BAD_CIDRS:
            self.assertRaises(ValidationError, ip.validate, cidr)

    def test_validate_mixed_cidr(self):
        GOOD_CIDRS = ("::ffff:0:0/56",
                      "2001:0db8::1428:57ab/17",
                      "FEC0::/10",
                      "fe80::204:61ff:254.157.241.86/4",
                      "fe80::204:61ff:254.157.241.86/0",
                      "2001:0DB8::CD30:0:0:0:0/60",
                      "0.0.0.0/16",
                      "10.144.11.107/4",
                      "255.255.255.255/0",
                      "0.1.2.3/16",
                      # short form
                      "128.0/16",
                      "10/4")
        BAD_CIDRS = ("1111:2222:3333:4444::://",
                     "::2222:3333:4444:5555:6666:7777:8888:",
                     ":1111:2222:3333:4444::6666:1.2.3.4/1/1",
                     "1111:2222::4444:5555:6666::8888\\2",
                     "1111:2222::4444:5555:6666:8888/",
                     "1111:2222::4444:5555:6666::8888/130",
                     "127.0.0.1/",
                     "127.0.0.1/33",
                     "127.0.0.1/-1")
        ip = forms.IPField(mask=True, version=forms.IPv4 | forms.IPv6)
        for cidr in GOOD_CIDRS:
            self.assertIsNone(ip.validate(cidr))
        for cidr in BAD_CIDRS:
            self.assertRaises(ValidationError, ip.validate, cidr)

    def test_validate_IPs(self):
        GOOD_IPS_V4 = ("0.0.0.0",
                       "10.144.11.107",
                       "169.144.11.107",
                       "172.100.11.107",
                       "255.255.255.255",
                       "0.1.2.3")
        GOOD_IPS_V6 = ("",
                       "::ffff:0:0",
                       "2001:0db8::1428:57ab",
                       "FEC0::",
                       "fe80::204:61ff:254.157.241.86",
                       "fe80::204:61ff:254.157.241.86",
                       "2001:0DB8::CD30:0:0:0:0")
        BAD_IPS_V4 = ("1111:2222:3333:4444:::",
                      "::2222:3333:4444:5555:6666:7777:8888:",
                      ":1111:2222:3333:4444::6666:1.2.3.4",
                      "1111:2222::4444:5555:6666::8888",
                      "1111:2222::4444:5555:6666:8888/",
                      "1111:2222::4444:5555:6666::8888/130",
                      "127.0.0.1/",
                      "127.0.0.1/33",
                      "127.0.0.1/-1")
        BAD_IPS_V6 = ("1111:2222:3333:4444:::",
                      "::2222:3333:4444:5555:6666:7777:8888:",
                      ":1111:2222:3333:4444::6666:1.2.3.4",
                      "1111:2222::4444:5555:6666::8888",
                      "1111:2222::4444:5555:6666:8888/",
                      "1111:2222::4444:5555:6666::8888/130")
        ipv4 = forms.IPField(version=forms.IPv4)
        ipv6 = forms.IPField(required=False, version=forms.IPv6)
        ipmixed = forms.IPField(required=False,
                                version=forms.IPv4 | forms.IPv6)

        for ip_addr in GOOD_IPS_V4:
            self.assertIsNone(ipv4.validate(ip_addr))
            self.assertIsNone(ipmixed.validate(ip_addr))

        for ip_addr in GOOD_IPS_V6:
            self.assertIsNone(ipv6.validate(ip_addr))
            self.assertIsNone(ipmixed.validate(ip_addr))

        for ip_addr in BAD_IPS_V4:
            self.assertRaises(ValidationError, ipv4.validate, ip_addr)
            self.assertRaises(ValidationError, ipmixed.validate, ip_addr)

        for ip_addr in BAD_IPS_V6:
            self.assertRaises(ValidationError, ipv6.validate, ip_addr)
            self.assertRaises(ValidationError, ipmixed.validate, ip_addr)

        self.assertRaises(ValidationError, ipv4.validate, "")  # required=True

        iprange = forms.IPField(required=False,
                                mask=True,
                                mask_range_from=10,
                                version=forms.IPv4 | forms.IPv6)
        self.assertRaises(ValidationError, iprange.validate,
                          "fe80::204:61ff:254.157.241.86/6")
        self.assertRaises(ValidationError, iprange.validate,
                          "169.144.11.107/8")
        self.assertIsNone(iprange.validate("fe80::204:61ff:254.157.241.86/36"))
        self.assertIsNone(iprange.validate("169.144.11.107/18"))

    def test_validate_multi_ip_field(self):
        GOOD_CIDRS_INPUT = ("192.168.1.1/16, 192.0.0.1/17",)
        BAD_CIDRS_INPUT = ("1.2.3.4.5/41,0.0.0.0/99",
                           "1.2.3.4.5/41;0.0.0.0/99",
                           "1.2.3.4.5/41   0.0.0.0/99",
                           "192.168.1.1/16 192.0.0.1/17")

        ip = forms.MultiIPField(mask=True, version=forms.IPv4)
        for cidr in GOOD_CIDRS_INPUT:
            self.assertIsNone(ip.validate(cidr))
        for cidr in BAD_CIDRS_INPUT:
            self.assertRaises(ValidationError, ip.validate, cidr)


class MACAddressFieldTests(test.TestCase):

    def test_mac_address_validator(self):
        GOOD_MAC_ADDRESSES = (
            "00:11:88:99:Aa:Ff",
            "00-11-88-99-Aa-Ff",
            "0011.8899.AaFf",
            "00118899AaFf",
        )
        BAD_MAC_ADDRESSES = (
            "not a mac",
            "11:22:33:44:55",
            "zz:11:22:33:44:55",
        )

        field = forms.MACAddressField()
        for input in GOOD_MAC_ADDRESSES:
            self.assertIsNone(field.validate(input))
        for input in BAD_MAC_ADDRESSES:
            self.assertRaises(ValidationError, field.validate, input)

    def test_mac_address_normal_form(self):
        field = forms.MACAddressField()
        field.validate("00-11-88-99-Aa-Ff")
        self.assertEqual(field.mac_address, "00:11:88:99:aa:ff")


class TestChoiceFieldForm(forms.SelfHandlingForm):
    title_dic = {"label1": {"title": "This is choice 1"},
                 "label2": {"title": "This is choice 2"},
                 "label3": {"title": "This is choice 3"}}
    name = forms.CharField(max_length=255,
                           label="Test Name",
                           help_text="Please enter a name")
    test_choices = forms.ChoiceField(
        label="Test Choices",
        required=False,
        help_text="Testing drop down choices",
        widget=forms.fields.SelectWidget(
            attrs={
                'class': 'switchable',
                'data-slug': 'source'},
            transform_html_attrs=title_dic.get))

    def __init__(self, request, *args, **kwargs):
        super(TestChoiceFieldForm, self).__init__(request, *args,
                                                  **kwargs)
        choices = ([('choice1', 'label1'),
                    ('choice2', 'label2')])
        self.fields['test_choices'].choices = choices

    def handle(self, request, data):
        return True


class ChoiceFieldTests(test.TestCase):

    template = 'horizon/common/_form_fields.html'

    def setUp(self):
        super(ChoiceFieldTests, self).setUp()
        self.form = TestChoiceFieldForm(self.request)

    def _render_form(self):
        return shortcuts.render(self.request, self.template,
                                {'form': self.form})

    def test_legacychoicefield_title(self):
        resp = self._render_form()
        self.assertContains(
            resp,
            '<option value="choice1" title="This is choice 1">label1</option>',
            count=1, html=True)
        self.assertContains(
            resp,
            '<option value="choice2" title="This is choice 2">label2</option>',
            count=1, html=True)


class TestThemableChoiceFieldForm(forms.SelfHandlingForm):
    # It's POSSIBLE to combine this with the test helper form above, but
    # I fear we'd run into collisions where one test's desired output is
    # actually within a separate widget's output.

    title_dic = {"label1": {"title": "This is choice 1"},
                 "label2": {"title": "This is choice 2"},
                 "label3": {"title": "This is choice 3"}}
    name = forms.CharField(max_length=255,
                           label="Test Name",
                           help_text="Please enter a name")
    test_choices = forms.ThemableChoiceField(
        label="Test Choices",
        required=False,
        help_text="Testing drop down choices",
        widget=forms.fields.ThemableSelectWidget(
            attrs={
                'class': 'switchable',
                'data-slug': 'source'},
            transform_html_attrs=title_dic.get))

    def __init__(self, request, *args, **kwargs):
        super(TestThemableChoiceFieldForm, self).__init__(request, *args,
                                                          **kwargs)
        choices = ([('choice1', 'label1'),
                    ('choice2', 'label2')])
        self.fields['test_choices'].choices = choices

    def handle(self, request, data):
        return True


class ThemableChoiceFieldTests(test.TestCase):

    template = 'horizon/common/_form_fields.html'

    def setUp(self):
        super(ThemableChoiceFieldTests, self).setUp()
        self.form = TestThemableChoiceFieldForm(self.request)

    def _render_form(self):
        return shortcuts.render(self.request, self.template,
                                {'form': self.form})

    def test_choicefield_labels_and_title_attr(self):
        resp = self._render_form()
        self.assertContains(
            resp,
            '<a data-select-value="choice1" title="This is choice 1">'
            'label1</a>',
            count=1,
            html=True)
        self.assertContains(
            resp,
            '<a data-select-value="choice2" title="This is choice 2">'
            'label2</a>',
            count=1,
            html=True)

    def test_choicefield_title_select_compatible(self):
        resp = self._render_form()
        self.assertContains(
            resp,
            '<option value="choice1" title="This is choice 1">label1</option>',
            count=1, html=True)
        self.assertContains(
            resp,
            '<option value="choice2" title="This is choice 2">label2</option>',
            count=1, html=True)
