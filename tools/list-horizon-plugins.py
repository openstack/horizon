#!/usr/bin/env python3
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

import argparse
import csv
import glob
import os

import yaml


# The script picks up deliverables whose type is 'horizon-plugin' in the
# openstack/releases repository. Some horizon plugins are released together
# with other repositories and we cannot pick them up for such case.
# EXTRA_PLUGINS is used to declare such horizon plugins.
# Each entry is a tuple of
# - the deliverable name in the releases repo, and
# - the repository name of the dashboard.
EXTRA_PLUGINS = {
    'networking-bgpvpn': 'networking-bgpvpn',
    'mistral': 'mistral-dashboard',
}


def read_plugin_data_from_releases(releases_repo, release):
    plugins = {}
    deliverables_glob = '%s/deliverables/%s/*.yaml' % (releases_repo, release)
    for deliverable in glob.glob(deliverables_glob):
        with open(deliverable) as f:
            data = yaml.safe_load(f)

        name = os.path.splitext(os.path.basename(deliverable))[0]
        if data['type'] == 'horizon-plugin':
            pass
        elif name in EXTRA_PLUGINS:
            name = EXTRA_PLUGINS[name]
        else:
            continue

        repos = [repo for repo in data['repository-settings']
                 if os.path.basename(repo) == name]
        if not repos:
            repos = list(data['repository-settings'].keys())[0]
        data['repository'] = repos[0]
        plugins[name] = data
    return plugins


def get_plugin_info(name, config):
    repo = ':opendev-repo:`%s`' % config['repository']
    if 'storyboard' in config:
        bug_tracker = ':storyboard:`%s`' % config['storyboard']
    elif 'launchpad' in config:
        bug_tracker = ':launchpad:`%s`' % config['launchpad']
    else:
        bug_tracker = None
    return [name, repo, bug_tracker]


def write_csv(plugins, csv_file):
    with open(csv_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, lineterminator='\n',
                               quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow(['Plugin', 'Repository', 'Bug Tracker'])
        for name in sorted(plugins):
            csvwriter.writerow(get_plugin_info(name, plugins[name]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--csv-file',
        default='plugin-registry.csv',
        help='Path to a CSV file which contains the plugin list.'
    )
    parser.add_argument(
        'repo',
        help='Path to openstack/releases repository cloned to local.'
    )
    parser.add_argument(
        'release',
        help='Release name like "ussuri'
    )
    args = parser.parse_args()
    plugins = read_plugin_data_from_releases(args.repo, args.release)

    write_csv(plugins, args.csv_file)


if __name__ == '__main__':
    main()
