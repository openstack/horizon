# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Copyright 2011 OpenStack LLC
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

version_info = {'branch_nick': u'LOCALBRANCH',
                'revision_id': 'LOCALREVISION',
                'revno': 0}


HORIZON_VERSION = ['2012', '1']
YEAR, COUNT = HORIZON_VERSION
FINAL = False   # This becomes true at Release Candidate time


def canonical_version_string():
    return '.'.join([YEAR, COUNT])


def version_string():
    if FINAL:
        return canonical_version_string()
    else:
        return '%s-dev' % (canonical_version_string(),)
