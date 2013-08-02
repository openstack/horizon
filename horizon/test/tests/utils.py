# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


import os

from django.core.exceptions import ValidationError  # noqa

from horizon.test import helpers as test
from horizon.utils import fields
from horizon.utils import secret_key


class ValidatorsTests(test.TestCase):
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
        ip = fields.IPField(mask=True, version=fields.IPv4)
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
        ip = fields.IPField(mask=True, version=fields.IPv6)
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
        ip = fields.IPField(mask=True, version=fields.IPv4 | fields.IPv6)
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
        ipv4 = fields.IPField(required=True, version=fields.IPv4)
        ipv6 = fields.IPField(required=False, version=fields.IPv6)
        ipmixed = fields.IPField(required=False,
                                 version=fields.IPv4 | fields.IPv6)

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

        iprange = fields.IPField(required=False,
                                 mask=True,
                                 mask_range_from=10,
                                 version=fields.IPv4 | fields.IPv6)
        self.assertRaises(ValidationError, iprange.validate,
                          "fe80::204:61ff:254.157.241.86/6")
        self.assertRaises(ValidationError, iprange.validate,
                          "169.144.11.107/8")
        self.assertIsNone(iprange.validate("fe80::204:61ff:254.157.241.86/36"))
        self.assertIsNone(iprange.validate("169.144.11.107/18"))


class SecretKeyTests(test.TestCase):
    def test_generate_secret_key(self):
        key = secret_key.generate_key(32)
        self.assertEqual(len(key), 32)
        self.assertNotEqual(key, secret_key.generate_key(32))

    def test_generate_or_read_key_from_file(self):
        key_file = ".test_secret_key_store"
        key = secret_key.generate_or_read_from_file(key_file)

        # Consecutive reads should come from the already existing file:
        self.assertEqual(key, secret_key.generate_or_read_from_file(key_file))

        # Key file only be read/writable by user:
        self.assertEqual(oct(os.stat(key_file).st_mode & 0o777), "0600")
        os.chmod(key_file, 0o777)
        self.assertRaises(secret_key.FilePermissionError,
                          secret_key.generate_or_read_from_file, key_file)
        os.remove(key_file)
