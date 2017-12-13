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

"""Tool to check policy file differeneces."""

from __future__ import print_function

import argparse

import yaml


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--old', required=True,
                        help='Current policy file')
    parser.add_argument('--new', required=True,
                        help='New policy file')
    parser.add_argument('--mode',
                        choices=['add', 'remove'],
                        default='remove',
                        help='Diffs to be shown')
    parsed_args = parser.parse_args()

    with open(parsed_args.old) as f:
        old_data = yaml.safe_load(f)

    with open(parsed_args.new) as f:
        new_data = yaml.safe_load(f)

    added = set(new_data.keys()) - set(old_data.keys())
    removed = set(old_data.keys()) - set(new_data.keys())

    if parsed_args.mode == 'remove':
        for key in sorted(removed):
            print(key)

    if parsed_args.mode == 'add':
        for key in sorted(added):
            print(key)


if __name__ == '__main__':
    main()
