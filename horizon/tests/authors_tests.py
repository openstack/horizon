# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack LLC
# Copyright 2012 Nebula Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import commands
import unittest


def parse_mailmap(mailmap='.mailmap'):
    mapping = {}
    if os.path.exists(mailmap):
        fp = open(mailmap, 'r')
        for l in fp:
            l = l.strip()
            if not l.startswith('#') and ' ' in l:
                canonical_email, alias = l.split(' ')
                mapping[alias] = canonical_email
    return mapping


def str_dict_replace(s, mapping):
    for s1, s2 in mapping.iteritems():
        s = s.replace(s1, s2)
    return s


class AuthorsTestCase(unittest.TestCase):
    def test_authors_up_to_date(self):
        path_bits = (os.path.dirname(__file__), '..', '..')
        root = os.path.normpath(os.path.join(*path_bits))
        contributors = set()
        missing = set()
        authors_file = open(os.path.join(root, 'AUTHORS'), 'r').read()

        if os.path.exists(os.path.join(root, '.git')):
            mailmap = parse_mailmap(os.path.join(root, '.mailmap'))
            for email in commands.getoutput('git log --format=%ae').split():
                if not email:
                    continue
                if "jenkins" in email and "openstack.org" in email:
                    continue
                email = '<' + email + '>'
                contributors.add(str_dict_replace(email, mailmap))

        for contributor in contributors:
            if not contributor in authors_file:
                missing.add(contributor)

        self.assertTrue(len(missing) == 0,
                        '%r not listed in AUTHORS file.' % missing)
