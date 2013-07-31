# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Red Hat, Inc.
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

from openstack_dashboard.openstack.common import processutils

def execute(*cmd, **kwargs):
    """Convenience wrapper around oslo's execute() method."""
    #TODO: Figure out how to make rootwrap.conf come from config
    if 'run_as_root' in kwargs and not 'root_helper' in kwargs:
        kwargs['root_helper'] =\
                'sudo openstack_dashboard-rootwrap /etc/openstack_dashboard/rootwrap.conf'

    return processutils.execute(*cmd, **kwargs)

