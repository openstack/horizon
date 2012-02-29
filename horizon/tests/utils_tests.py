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


from horizon import test
from horizon.utils import validators


class ValidatorsTests(test.TestCase):
    def test_validate_ipv4_cidr(self):
        GOOD_CIDRS = ("192.168.1.1/16",
                      "192.0.0.1/17",
                      "0.0.0.0/16",
                      "10.144.11.107/4",
                      "255.255.255.255/0",
                      "0.1.2.3/16",
                      "0.0.0.0/32")
        BAD_CIDRS = ("255.255.255.256",
                     "256.255.255.255",
                     "1.2.3.4.5",
                     "0.0.0.0",
                     "127.0.0.1/",
                     "127.0.0.1/33",
                     "127.0.0.1/-1",
                     "127.0.0.1/100")
        for cidr in GOOD_CIDRS:
            self.assertTrue(validators.ipv4_cidr_re.match(cidr))
        for cidr in BAD_CIDRS:
            self.assertFalse(validators.ipv4_cidr_re.match(cidr))
