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

from horizon.test import helpers as test
from horizon.utils import validators


class ValidatorsTests(test.TestCase):

    def test_port_validator(self):
        VALID_PORTS = (1, 65535)
        INVALID_PORTS = (-1, 65536)

        for port in VALID_PORTS:
            self.assertIsNone(validators.validate_port_range(port))

        for port in INVALID_PORTS:
            self.assertRaises(ValidationError,
                              validators.validate_port_range,
                              port)

    def test_icmp_type_validator(self):
        VALID_ICMP_TYPES = (1, 0, 255, -1)
        INVALID_ICMP_TYPES = (256, None, -2)

        for icmp_type in VALID_ICMP_TYPES:
            self.assertIsNone(validators.validate_icmp_type_range(icmp_type))

        for icmp_type in INVALID_ICMP_TYPES:
            self.assertRaises(ValidationError,
                              validators.validate_icmp_type_range,
                              icmp_type)

    def test_icmp_code_validator(self):
        VALID_ICMP_CODES = (1, 0, 255, None, -1,)
        INVALID_ICMP_CODES = (256, -2)

        for icmp_code in VALID_ICMP_CODES:
            self.assertIsNone(validators.validate_icmp_code_range(icmp_code))

        for icmp_code in INVALID_ICMP_CODES:
            self.assertRaises(ValidationError,
                              validators.validate_icmp_code_range,
                              icmp_code)

    def test_ip_proto_validator(self):
        VALID_PROTO = (0, 255, -1)
        INVALID_PROTO = (-2, 256)

        for proto in VALID_PROTO:
            self.assertIsNone(validators.validate_ip_protocol(proto))

        for proto in INVALID_PROTO:
            self.assertRaises(ValidationError,
                              validators.validate_ip_protocol,
                              proto)

    def test_port_range_validator(self):
        VALID_RANGE = ('1:65535',
                       '1:1')
        INVALID_RANGE = ('22:22:22:22',
                         '1:-1',
                         '-1:65535')

        test_call = validators.validate_port_or_colon_separated_port_range
        for prange in VALID_RANGE:
            self.assertIsNone(test_call(prange))

        for prange in INVALID_RANGE:
            self.assertRaises(ValidationError, test_call, prange)

    def test_metadata_validator(self):
        VALID_METADATA = (
            "key1=val1", "key1=val1,key2=val2",
            "key1=val1,key2=val2,key3=val3", "key1="
        )
        INVALID_METADATA = (
            "key1==val1", "key1=val1,", "=val1",
            "=val1", "  "
        )

        for mdata in VALID_METADATA:
            self.assertIsNone(validators.validate_metadata(mdata))

        for mdata in INVALID_METADATA:
            self.assertRaises(ValidationError,
                              validators.validate_metadata,
                              mdata)
