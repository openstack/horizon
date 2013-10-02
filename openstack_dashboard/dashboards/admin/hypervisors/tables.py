# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 B1 Systems GmbH
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

from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import tables
from horizon.templatetags import sizeformat


def get_memory(hypervisor):
    return sizeformat.mbformat(hypervisor.memory_mb)


def get_memory_used(hypervisor):
    return sizeformat.mbformat(hypervisor.memory_mb_used)


def get_local(hypervisor):
    return sizeformat.diskgbformat(hypervisor.local_gb)


def get_local_used(hypervisor):
    return sizeformat.diskgbformat(hypervisor.local_gb_used)


class AdminHypervisorsTable(tables.DataTable):
    hypervisor_hostname = tables.Column("hypervisor_hostname",
                                        verbose_name=_("Hostname"))

    hypervisor_type = tables.Column("hypervisor_type",
                                    verbose_name=_("Type"))

    vcpus = tables.Column("vcpus",
                          verbose_name=_("VCPUs (total)"))

    vcpus_used = tables.Column("vcpus_used",
                               verbose_name=_("VCPUs (used)"))

    memory = tables.Column(get_memory,
                           verbose_name=_("RAM (total)"),
                           attrs={'data-type': 'size'})

    memory_used = tables.Column(get_memory_used,
                                verbose_name=_("RAM (used)"),
                                attrs={'data-type': 'size'})

    local = tables.Column(get_local,
                          verbose_name=_("Storage (total)"),
                          attrs={'data-type': 'size'})

    local_used = tables.Column(get_local_used,
                               verbose_name=_("Storage (used)"),
                               attrs={'data-type': 'size'})

    running_vms = tables.Column("running_vms",
                                verbose_name=_("Instances"))

    class Meta:
        name = "hypervisors"
        verbose_name = _("Hypervisors")
