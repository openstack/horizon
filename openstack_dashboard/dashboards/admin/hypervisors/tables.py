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


from horizon import tables
from horizon.templatetags import sizeformat
from django.utils.translation import gettext_lazy as _
from functools import lru_cache
import ipaddress
import socket
from django.conf import settings
from openstack_dashboard import api
from django.urls import reverse
from urllib.parse import quote



################ xloud code ################
def _looks_like_ip(s: str) -> bool:
    try:
        ipaddress.ip_address(s)
        return True
    except Exception:
        return False

@lru_cache(maxsize=512)
def _dns_resolve(host: str) -> str | None:
    try:
        return socket.gethostbyname(host)
    except Exception:
        return None

def _nova_resolve_ip(request, host_or_name: str) -> str | None:
    """Ask Nova for host_ip of the hypervisor matching this name."""
    try:
        hypers = api.nova.hypervisor_search(request, host_or_name) or []
        for h in hypers:
            ip = getattr(h, "host_ip", None)
            if ip:
                return ip
        # sometimes hypervisor_hostname is already an IP
        if hypers:
            hh = getattr(hypers[0], "hypervisor_hostname", None)
            if hh and _looks_like_ip(hh):
                return hh
    except Exception:
        pass
    return None

class OpenLocalAppModal(tables.LinkAction):  # keep the name your table references
    name = "open_local_app_popup"
    verbose_name = _("Host Management")
    classes = ("btn", "btn-default")
    icon = "link"

    def _resolve_ip(self, request, datum) -> str | None:
        # 1) exact field from the row
        ip = getattr(datum, "host_ip", None)
        if ip and _looks_like_ip(ip):
            return ip

        # 2) try nova by the hypervisor name/host
        host_name = (getattr(datum, "hypervisor_hostname", None)
                     or getattr(datum, "host", None)
                     or "")
        if host_name:
            ip = _nova_resolve_ip(request, host_name)
            if ip:
                return ip

        # 3) DNS fallback if the "host" looks like a name
        if host_name and not _looks_like_ip(host_name):
            ip = _dns_resolve(host_name)
            if ip:
                return ip

        # 4) last resort: if the hypervisor_hostname is itself an IP
        if host_name and _looks_like_ip(host_name):
            return host_name
        return None

    def get_link_url(self, datum):
        request = self.table.request

        ip = self._resolve_ip(request, datum)
        if not ip:
            # No IP → don’t emit a broken link
            return None

        scheme = getattr(settings, "OPEN_LOCAL_APP_SCHEME", "https")
        port   = getattr(settings, "OPEN_LOCAL_APP_PORT", 10000)
        path   = getattr(settings, "OPEN_LOCAL_APP_PATH", "/")
        if not path.startswith("/"):
            path = "/" + path

        # IPv6 needs brackets
        host_for_url = f"[{ip}]" if (":" in ip and ip.count(":") > 1) else ip
        return f"{scheme}://{host_for_url}:{port}{path}"

    def get_default_attrs(self):
        # open in popup (falls back to new tab if blocked)
        attrs = super().get_default_attrs()
        attrs["onclick"] = (
            "window.open(this.href,'hostapp',"
            "'noopener,noreferrer,width=1200,height=800,menubar=0,toolbar=0');"
            "return false;"
        )
        attrs["target"] = "_blank"
        attrs["rel"] = "noopener noreferrer"
        return attrs
        
    #######################################


class AdminHypervisorsTable(tables.DataTable):
    hostname = tables.WrappingColumn("hypervisor_hostname",
                                     link="horizon:admin:hypervisors:detail",
                                     verbose_name=_("Hostname"))
    hypervisor_type = tables.Column("hypervisor_type",
                                    verbose_name=_("Type"))
    memory_used = tables.Column('memory_mb_used',
                                verbose_name=_("RAM (used)"),
                                attrs={'data-type': 'size'},
                                filters=(sizeformat.mb_float_format,))
    memory = tables.Column('memory_mb',
                           verbose_name=_("RAM (total)"),
                           attrs={'data-type': 'size'},
                           filters=(sizeformat.mb_float_format,))
    local_used = tables.Column('local_gb_used',
                               verbose_name=_("Local Storage (used)"),
                               attrs={'data-type': 'size'},
                               filters=(sizeformat.diskgbformat,))
    local = tables.Column('local_gb',
                          verbose_name=_("Local Storage (total)"),
                          attrs={'data-type': 'size'},
                          filters=(sizeformat.diskgbformat,))
    running_vms = tables.Column("running_vms",
                                verbose_name=_("Instances"))

    def get_object_id(self, hypervisor):
        return "%s_%s" % (hypervisor.id,
                          hypervisor.hypervisor_hostname)

    class Meta(object):
        name = "hypervisors"
        verbose_name = _("Hypervisors")
        row_actions = (
            OpenLocalAppModal,
        )


class AdminHypervisorInstancesTable(tables.DataTable):
    name = tables.WrappingColumn("name",
                                 link="horizon:admin:instances:detail",
                                 verbose_name=_("Instance Name"))

    instance_id = tables.Column("uuid",
                                verbose_name=_("Instance ID"))

    def get_object_id(self, server):
        return server['uuid']

    class Meta(object):
        name = "hypervisor_instances"
        verbose_name = _("Hypervisor Instances")


class AdminProvidersTable(tables.DataTable):
    name = tables.WrappingColumn("name",
                                 verbose_name=_("Resource Provider Name"))
    vcpus_used = tables.Column("vcpus_used",
                               verbose_name=_("VCPUs used"))
    vcpus_reserved = tables.Column("vcpus_reserved",
                                   verbose_name=_("VCPUs reserved"))
    vcpus = tables.Column("vcpus",
                          verbose_name=_("VCPUs total"))
    vcpus_ar = tables.Column("vcpus_ar",
                             verbose_name=_("VCPUs allocation ratio"))
    pcpus_used = tables.Column("pcpus_used",
                               verbose_name=_("PCPUs used"))
    pcpus_reserved = tables.Column("pcpus_reserved",
                                   verbose_name=_("PCPUs reserved"))
    pcpus = tables.Column("pcpus",
                          verbose_name=_("PCPUs total"))
    pcpus_ar = tables.Column("pcpus_ar",
                             verbose_name=_("PCPUs allocation ratio"))
    memory_used = tables.Column("memory_mb_used",
                                verbose_name=_("RAM used"),
                                attrs={'data-type': 'size'},
                                filters=(sizeformat.mb_float_format,))
    memory_reserved = tables.Column("memory_mb_reserved",
                                    verbose_name=_("RAM reserved"),
                                    attrs={'data-type': 'size'},
                                    filters=(sizeformat.mb_float_format,))
    memory = tables.Column("memory_mb",
                           verbose_name=_("RAM total"),
                           attrs={'data-type': 'size'},
                           filters=(sizeformat.mb_float_format,))
    memory_ar = tables.Column("memory_mb_ar",
                              verbose_name=_("RAM allocation ratio"))
    disk_used = tables.Column("disk_gb_used",
                              verbose_name=_("Storage used"),
                              attrs={'data-type': 'size'},
                              filters=(sizeformat.diskgbformat,))
    disk_reserved = tables.Column("disk_gb_reserved",
                                  verbose_name=_("Storage reserved"),
                                  attrs={'data-type': 'size'},
                                  filters=(sizeformat.diskgbformat,))
    disk = tables.Column("disk_gb",
                         verbose_name=_("Storage total"),
                         attrs={'data-type': 'size'},
                         filters=(sizeformat.diskgbformat,))
    disk_ar = tables.Column("disk_gb_ar",
                            verbose_name=_("Storage allocation ratio"))

    def get_object_id(self, provider):
        return provider['uuid']

    class Meta(object):
        name = "providers"
        verbose_name = _("Resource Providers")
