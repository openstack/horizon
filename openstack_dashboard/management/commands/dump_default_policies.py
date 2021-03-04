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

import logging
import sys

from django.core.management.base import BaseCommand
from oslo_policy import generator
import yaml


LOG = logging.getLogger(__name__)


def _load_default_policies(namespace):
    defaults = generator.get_policies_dict([namespace])
    return defaults.get(namespace)


def _format_default_policy(default):
    data = {
        'name': default.name,
        'check_str': default.check_str,
        'description': default.description,
    }
    data['operations'] = getattr(default, 'operations', [])
    data['scope_types'] = getattr(default, 'scope_types', None)

    if default.deprecated_for_removal:
        data['deprecated_for_removal'] = True
        data['deprecated_since'] = default.deprecated_since
        data['deprecated_reason'] = default.deprecated_reason

    if default.deprecated_rule:
        data['deprecated_rule'] = {
            'name': default.deprecated_rule.name,
            'check_str': default.deprecated_rule.check_str,
        }
        data['deprecated_since'] = default.deprecated_since
        data['deprecated_reason'] = default.deprecated_reason

    return data


def _write_yaml_file(policies, output_file):
    stream = open(output_file, 'w') if output_file else sys.stdout
    yaml.dump(policies, stream=stream)
    if output_file:
        stream.close()


class Command(BaseCommand):
    help = ("Dump default policies of back-end services defined in codes "
            "as YAML file so that horizon can load default policies.")

    def add_arguments(self, parser):
        parser.add_argument(
            '--namespace',
            required=True,
            help='Namespace under "oslo.policy.policies" to query.')
        parser.add_argument(
            '--output-file',
            help='Path of the file to write to. Defaults to stdout.')

    def handle(self, *args, **options):
        namespace = options['namespace']
        defaults = _load_default_policies(namespace)
        if defaults is None:
            LOG.error('The requested namespace "%s" is not found.', namespace)
            sys.exit(1)

        policies = [_format_default_policy(default) for default in defaults]
        _write_yaml_file(policies, options['output_file'])
