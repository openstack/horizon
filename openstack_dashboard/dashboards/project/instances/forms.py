# Copyright 2013 OpenStack Foundation
# All Rights Reserved.
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

from django.core.validators import MaxValueValidator, MinValueValidator



from django import forms
from django.template.defaultfilters import filesizeformat
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.decorators.debug import sensitive_variables

from horizon import exceptions, messages
from horizon import forms as h_forms
from horizon.forms import fields as hz_fields
from horizon.forms import widgets as hz_widgets
from horizon import forms as hz_forms
from django.urls import reverse_lazy
# ---- Hard shims so legacy attribute lookups won't explode anywhere ----
if not hasattr(hz_widgets, 'ThemableSelectWidget'):
    # Let Horizon think the “themed” widget exists; use plain Select.
    setattr(hz_widgets, 'ThemableSelectWidget', forms.Select)

if not hasattr(hz_fields, 'ThemableChoiceField'):
    # Same idea for the field class; fall back to Django's ChoiceField
    setattr(hz_fields, 'ThemableChoiceField', forms.ChoiceField)


# ---- Horizon compat shims (works with and without Themable* classes) ----
# Select/Choice fallbacks
ThemedChoiceField = getattr(hz_fields, 'ThemableChoiceField', forms.ChoiceField)
ThemedSelectWidget = getattr(hz_widgets, 'ThemableSelectWidget', forms.Select)

# (Optional) IPField fallback, if your Horizon doesn't provide it
IPField = getattr(hz_fields, 'IPField', None)
IPv4 = getattr(hz_fields, 'IPv4', None)
IPv6 = getattr(hz_fields, 'IPv6', None)
# ---- End Horizon compat shims ----

# Helper to build a select widget compatible with both horizons
def make_select_widget(**kwargs):
    """
    If ThemedSelectWidget is the Horizon widget, it supports extra kwargs
    like data_attrs/transform. If it's falling back to django.forms.Select,
    only pass attrs.
    """
    if ThemedSelectWidget is forms.Select:
        return ThemedSelectWidget(attrs=kwargs.get('attrs', {}))
    return ThemedSelectWidget(**kwargs)

# ---- IP field factory (works with or without Horizon's IPField) ----
def make_ip_field(*, attrs):
    if IPField and IPv4 and IPv6:
        # Horizon provides a richer IPField
        return IPField(
            label=_("Fixed IP Address"),
            required=False,
            help_text=_("IP address for the new port"),
            version=IPv4 | IPv6,
            widget=forms.TextInput(attrs=attrs),
        )
    # Fallback to Django’s GenericIPAddressField
    return forms.GenericIPAddressField(
        label=_("Fixed IP Address"),
        required=False,
        help_text=_("IP address for the new port"),
        protocol="both",
        widget=forms.TextInput(attrs=attrs),
    )

# Build the actual field instance once so the class can reference it
_fixed_ip_field = make_ip_field(attrs={
    'class': 'switched',
    'data-switch-on': 'specification_method',
    'data-specification_method-network': _('Fixed IP Address'),
})

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from collections import OrderedDict
from openstack_dashboard.api import keystone as api_keystone
from openstack_dashboard.api import base as api_base
from openstack_dashboard import api
from openstack_dashboard.dashboards.project.images import utils as image_utils
from openstack_dashboard.dashboards.project.instances import utils as instance_utils
from horizon.utils import validators
import logging
LOG = logging.getLogger(__name__)

def _image_choice_title(img):
    gb = filesizeformat(img.size)
    return '%s (%s)' % (img.name or img.id, gb)


class RebuildInstanceForm(h_forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())

    image = forms.ChoiceField(
        label=_("Select Image"),
        widget=make_select_widget(
            attrs={'class': 'image-selector'},
            data_attrs=('size', 'display-name'),
            transform=_image_choice_title,
        ),
    )
    password = forms.RegexField(
        label=_("Rebuild Password"),
        required=False,
        widget=forms.PasswordInput(render_value=False),
        regex=validators.password_validator(),
        error_messages={'invalid': validators.password_validator_msg()},
    )
    confirm_password = forms.CharField(
        label=_("Confirm Rebuild Password"),
        required=False,
        strip=False,
        widget=forms.PasswordInput(render_value=False),
    )
    disk_config = forms.ChoiceField(
        label=_("Disk Partition"),
        choices=[("AUTO", _("Automatic")), ("MANUAL", _("Manual"))],
        required=False,
    )
    description = forms.CharField(
        label=_("Description"),
        widget=forms.Textarea(attrs={'rows': 4}),
        max_length=255,
        required=False,
    )

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)

        if not api.nova.is_feature_available(request, "instance_description"):
            del self.fields['description']

        instance_id = kwargs.get('initial', {}).get('instance_id')
        self.fields['instance_id'].initial = instance_id

        images = image_utils.get_available_images(request, request.user.tenant_id)
        choices = [(image.id, image) for image in images]
        if choices:
            choices.insert(0, ("", _("Select Image")))
        else:
            choices.insert(0, ("", _("No images available")))
        self.fields['image'].choices = choices

        if not api.nova.can_set_server_password():
            del self.fields['password']
            del self.fields['confirm_password']

    def clean(self):
        cleaned_data = super().clean()
        if 'password' in cleaned_data:
            passwd = cleaned_data.get('password')
            confirm = cleaned_data.get('confirm_password')
            if passwd is not None and confirm is not None:
                if passwd != confirm:
                    raise forms.ValidationError(_("Passwords do not match."))
        return cleaned_data

    # We have to protect the entire "data" dict because it contains the
    # password and confirm_password strings.
    @sensitive_variables('data', 'password')
    def handle(self, request, data):
        instance = data.get('instance_id')
        image = data.get('image')
        password = data.get('password') or None
        disk_config = data.get('disk_config', None)
        description = data.get('description', None)
        try:
            api.nova.server_rebuild(
                request, instance, image, password, disk_config, description=description
            )
            messages.info(request, _('Rebuilding instance %s.') % instance)
        except Exception:
            redirect = reverse('horizon:project:instances:index')
            exceptions.handle(request, _("Unable to rebuild instance."), redirect=redirect)
        return True


class DecryptPasswordInstanceForm(h_forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())
    _keypair_name_label = _("Key Pair Name")
    _keypair_name_help = _("The Key Pair name that was associated with the instance")
    _attrs = {'readonly': 'readonly', 'rows': 4}
    keypair_name = forms.CharField(
        widget=forms.widgets.TextInput(_attrs),
        label=_keypair_name_label,
        help_text=_keypair_name_help,
        required=False,
    )
    _encrypted_pwd_help = _("The instance password encrypted with your public key.")
    encrypted_password = forms.CharField(
        widget=forms.widgets.Textarea(_attrs),
        label=_("Encrypted Password"),
        help_text=_encrypted_pwd_help,
        strip=False,
        required=False,
    )

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        instance_id = kwargs.get('initial', {}).get('instance_id')
        self.fields['instance_id'].initial = instance_id
        keypair_name = kwargs.get('initial', {}).get('keypair_name')
        self.fields['keypair_name'].initial = keypair_name
        try:
            result = api.nova.get_password(request, instance_id)
            if not result:
                _unavailable = _("Instance Password is not set or is not yet available")
                self.fields['encrypted_password'].initial = _unavailable
            else:
                self.fields['encrypted_password'].initial = result
                self.fields['private_key_file'] = forms.FileField(
                    label=_('Private Key File'),
                    widget=forms.FileInput(),
                )
                self.fields['private_key'] = forms.CharField(
                    widget=forms.widgets.Textarea(),
                    label=_("OR Copy/Paste your Private Key"),
                )
                _attrs = {'readonly': 'readonly'}
                self.fields['decrypted_password'] = forms.CharField(
                    widget=forms.widgets.TextInput(_attrs),
                    label=_("Password"),
                    required=False,
                )
        except Exception:
            redirect = reverse('horizon:project:instances:index')
            _error = _("Unable to retrieve instance password.")
            exceptions.handle(request, _error, redirect=redirect)

    def handle(self, request, data):
        return True


class AttachVolume(h_forms.SelfHandlingForm):
    volume = forms.ChoiceField(
        label=_("Volume ID"),
        widget=ThemedSelectWidget(),
        help_text=_("Select a volume to attach to this instance."),
    )
    device = forms.CharField(
        label=_("Device Name"),
        widget=forms.HiddenInput(),
        required=False,
        help_text=_(
            "Actual device name may differ due to hypervisor settings. "
            "If not specified, then hypervisor will select a device name."
        ),
    )
    instance_id = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)

        # Populate volume choices
        volume_list = kwargs.get('initial', {}).get("volume_list", [])
        volumes = []
        for volume in volume_list:
            # Only show volumes that aren't attached to an instance already
            # Or those with multiattach enabled
            if (not volume.attachments or
                    (getattr(volume, 'multiattach', False)) and
                    api.nova.get_microversion(request, 'multiattach')):
                volumes.append(
                    (volume.id, '%(name)s (%(id)s)' % {"name": volume.name, "id": volume.id})
                )
        if volumes:
            volumes.insert(0, ("", _("Select a volume")))
        else:
            volumes.insert(0, ("", _("No volumes available")))
        self.fields['volume'].choices = volumes

    def handle(self, request, data):
        instance_id = self.initial.get("instance_id", None)
        volume_choices = dict(self.fields['volume'].choices)
        volume = volume_choices.get(data['volume'], _("Unknown volume (None)"))
        volume_id = data.get('volume')
        device = data.get('device') or None

        try:
            attach = api.nova.instance_volume_attach(request, volume_id, instance_id, device)
            message = _('Attaching volume %(vol)s to instance %(inst)s on %(dev)s.') % {
                "vol": volume, "inst": instance_id, "dev": attach.device
            }
            messages.info(request, message)
        except Exception:
            redirect = reverse('horizon:project:instances:index')
            msg = _('Unable to attach volume.')
            exceptions.handle(request, msg, redirect=redirect)
        return True


class DetachVolume(h_forms.SelfHandlingForm):
    volume = forms.ChoiceField(
        label=_("Volume ID"),
        widget=ThemedSelectWidget(),
        help_text=_("Select a volume to detach from this instance."),
    )
    instance_id = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate instance id
        instance_id = kwargs.get('initial', {}).get("instance_id", None)

        # Populate attached volumes
        try:
            volumes = []
            volume_list = api.nova.instance_volumes_list(self.request, instance_id)
            for volume in volume_list:
                volumes.append((volume.id, '%s (%s)' % (volume.name, volume.id)))
            if volume_list:
                volumes.insert(0, ("", _("Select a volume")))
            else:
                volumes.insert(0, ("", _("No volumes attached")))

            self.fields['volume'].choices = volumes
        except Exception:
            redirect = reverse('horizon:project:instances:index')
            exceptions.handle(self.request, _("Unable to detach volume."), redirect=redirect)

    def handle(self, request, data):
        instance_id = self.initial.get("instance_id", None)
        volume_choices = dict(self.fields['volume'].choices)
        volume = volume_choices.get(data['volume'], _("Unknown volume (None)"))
        volume_id = data.get('volume')

        try:
            api.nova.instance_volume_detach(request, instance_id, volume_id)
            message = _('Detaching volume %(vol)s from instance %(inst)s.') % {
                "vol": volume, "inst": instance_id
            }
            messages.info(request, message)
        except Exception:
            redirect = reverse('horizon:project:instances:index')
            exceptions.handle(request, _("Unable to detach volume."), redirect=redirect)
        return True


class AttachInterface(h_forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())
    specification_method = ThemedChoiceField(
        label=_("The way to specify an interface"),
        initial=False,
        widget=ThemedSelectWidget(attrs={
            'class': 'switchable',
            'data-slug': 'specification_method',
        }),
    )
    port = ThemedChoiceField(
        label=_("Port"),
        required=False,
        widget=ThemedSelectWidget(attrs={
            'class': 'switched',
            'data-required-when-shown': 'true',
            'data-switch-on': 'specification_method',
            'data-specification_method-port': _('Port'),
        }),
    )
    network = ThemedChoiceField(
        label=_("Network"),
        required=False,
        widget=ThemedSelectWidget(attrs={
            'class': 'switched',
            'data-required-when-shown': 'true',
            'data-switch-on': 'specification_method',
            'data-specification_method-network': _('Network'),
        }),
    )
    fixed_ip = _fixed_ip_field


    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        networks = instance_utils.network_field_data(
            request, include_empty_option=True, with_cidr=True
        )
        self.fields['network'].choices = networks

        choices = [('network', _("by Network (and IP address)"))]
        ports = instance_utils.port_field_data(request, with_network=True)
        if ports:
            self.fields['port'].choices = ports
            choices.append(('port', _("by Port")))
        self.fields['specification_method'].choices = choices

    def clean_network(self):
        specification_method = self.cleaned_data.get('specification_method')
        network = self.cleaned_data.get('network')
        if specification_method == 'network' and not network:
            msg = _('This field is required.')
            self._errors['network'] = self.error_class([msg])
        return network

    def handle(self, request, data):
        instance_id = data['instance_id']
        try:
            net_id = port_id = fixed_ip = None
            if data['specification_method'] == 'port':
                port_id = data.get('port')
            else:
                net_id = data.get('network')
                if data.get('fixed_ip'):
                    fixed_ip = data.get('fixed_ip')
            api.nova.interface_attach(
                request, instance_id, net_id=net_id, fixed_ip=fixed_ip, port_id=port_id
            )
            msg = _('Attaching interface for instance %s.') % instance_id
            messages.success(request, msg)
        except Exception:
            redirect = reverse('horizon:project:instances:index')
            exceptions.handle(request, _("Unable to attach interface."), redirect=redirect)
        return True


class DetachInterface(h_forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())
    port = ThemedChoiceField(label=_("Port"))

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        instance_id = self.initial.get("instance_id", None)

        ports = []
        try:
            ports = api.neutron.port_list(request, device_id=instance_id)
        except Exception:
            exceptions.handle(request, _('Unable to retrieve ports information.'))

        choices = []
        for port in ports:
            ips = []
            for ip in port.fixed_ips:
                ips.append(ip['ip_address'])
            choices.append((port.id, ','.join(ips) or port.id))
        if choices:
            choices.insert(0, ("", _("Select Port")))
        else:
            choices.insert(0, ("", _("No Ports available")))
        self.fields['port'].choices = choices

    def handle(self, request, data):
        instance_id = data['instance_id']
        port = data.get('port')
        try:
            api.nova.interface_detach(request, instance_id, port)
            msg = _('Detached interface %(port)s for instance %(instance)s.') % {
                'port': port, 'instance': instance_id
            }
            messages.success(request, msg)
        except Exception:
            redirect = reverse('horizon:project:instances:index')
            exceptions.handle(request, _("Unable to detach interface."), redirect=redirect)
        return True


class Disassociate(h_forms.SelfHandlingForm):
    fip = ThemedChoiceField(label=_('Floating IP'))
    is_release = forms.BooleanField(label=_('Release Floating IP'), required=False)

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        instance_id = self.initial['instance_id']
        targets = api.neutron.floating_ip_target_list_by_instance(request, instance_id)
        target_ids = [t.port_id for t in targets]

        self.fips = [
            fip for fip in api.neutron.tenant_floating_ip_list(request)
            if fip.port_id in target_ids
        ]

        fip_choices = [(fip.id, fip.ip) for fip in self.fips]
        fip_choices.insert(0, ('', _('Select a floating IP to disassociate')))
        self.fields['fip'].choices = fip_choices
        self.fields['fip'].initial = self.fips[0].id if self.fips else ''

    def handle(self, request, data):
        redirect = reverse_lazy('horizon:project:instances:index')
        fip_id = data['fip']
        fips = [fip for fip in self.fips if fip.id == fip_id]
        if not fips:
            messages.error(request, _("The specified floating IP no longer exists."))
            raise exceptions.Http302(redirect)
        fip = fips[0]
        try:
            if data['is_release']:
                api.neutron.tenant_floating_ip_release(request, fip_id)
                messages.success(
                    request,
                    _("Successfully disassociated and released floating IP %s") % fip.ip,
                )
            else:
                api.neutron.floating_ip_disassociate(request, fip_id)
                messages.success(
                    request,
                    _("Successfully disassociated floating IP %s") % fip.ip,
                )
        except Exception:
            exceptions.handle(
                request, _('Unable to disassociate floating IP %s') % fip.ip, redirect=redirect
            )
        return True


class RescueInstanceForm(h_forms.SelfHandlingForm):
    image = forms.ChoiceField(
        label=_("Select Image"),
        widget=make_select_widget(
            attrs={'class': 'image-selector'},
            data_attrs=('size', 'display-name'),
            transform=_image_choice_title,
        ),
    )
    password = forms.CharField(
        label=_("Password"),
        max_length=255,
        required=False,
        strip=False,
        widget=forms.PasswordInput(render_value=False),
    )
    failure_url = 'horizon:project:instances:index'

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        images = image_utils.get_available_images(request, request.user.tenant_id)
        choices = [(image.id, image) for image in images]
        if not choices:
            choices.insert(0, ("", _("No images available")))
        self.fields['image'].choices = choices

    def handle(self, request, data):
        try:
            api.nova.server_rescue(
                request,
                self.initial["instance_id"],
                password=data["password"],
                image=data["image"],
            )
            messages.success(request, _('Successfully rescued instance'))
            return True
        except Exception:
            redirect = reverse(self.failure_url)
            exceptions.handle(request, _('Unable to rescue instance'), redirect=redirect)

###################################################################################################################################
# ---------- xloud code ----------

class AdjustVcpuRamForm(h_forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())
    current_vcpus = forms.IntegerField(required=False, min_value=1)
    current_memory_mb = forms.IntegerField(required=False, min_value=1)
    persist = forms.BooleanField(required=False, initial=True)

    # discovered bounds
    _max_vcpus = None
    _max_mem_mb = None
    _min_vcpus = None
    _min_mem_mb = None

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)

        inst_id = kwargs.get("initial", {}).get("instance_id")
        try:
            inst = api.nova.server_get(request, inst_id)

            # Resolve current flavor
            flavors = api.nova.flavor_list(request)
            flavor_map = OrderedDict((str(f.id), f) for f in flavors)
            flavor = instance_utils.resolve_flavor(request, inst, flavor_map)

            # Upper bounds from flavor capacity
            self._max_vcpus = getattr(flavor, "vcpus", None)
            self._max_mem_mb = getattr(flavor, "ram", None)  # MB

            # Lower bounds from flavor extra specs (minimum_cpu/memory)
            specs = {}
            try:
                specs = api.nova.flavor_get_extras(request, flavor.id, raw=True) or {}
            except Exception:
                specs = getattr(flavor, "extra_specs", {}) or {}
                if not specs and hasattr(flavor, "get_keys"):
                    try:
                        specs = flavor.get_keys() or {}
                    except Exception:
                        specs = {}

            def _to_int(val):
                try:
                    return int(str(val).strip())
                except Exception:
                    return None

            self._min_vcpus = _to_int(specs.get("minimum_cpu"))
            self._min_mem_mb = _to_int(specs.get("minimum_memory"))

            # sanity: don’t let mins exceed maxes
            if self._min_vcpus and self._max_vcpus and self._min_vcpus > self._max_vcpus:
                LOG.warning("minimum_cpu (%s) > flavor vcpus (%s); ignoring minimum.",
                            self._min_vcpus, self._max_vcpus)
                self._min_vcpus = None
            if self._min_mem_mb and self._max_mem_mb and self._min_mem_mb > self._max_mem_mb:
                LOG.warning("minimum_memory (%s) > flavor ram (%s); ignoring minimum.",
                            self._min_mem_mb, self._max_mem_mb)
                self._min_mem_mb = None

            # validators + HTML min/max + help_text
            if self._min_vcpus:
                self.fields["current_vcpus"].validators.append(
                    MinValueValidator(self._min_vcpus, message=_("Must be ≥ %(limit)s vCPUs"))
                )
                self.fields["current_vcpus"].widget.attrs["min"] = self._min_vcpus
            if self._max_vcpus:
                self.fields["current_vcpus"].validators.append(
                    MaxValueValidator(self._max_vcpus, message=_("Must be ≤ %(limit)s vCPUs"))
                )
                self.fields["current_vcpus"].widget.attrs["max"] = self._max_vcpus

            if self._min_mem_mb:
                self.fields["current_memory_mb"].validators.append(
                    MinValueValidator(self._min_mem_mb, message=_("Must be ≥ %(limit)s MB"))
                )
                self.fields["current_memory_mb"].widget.attrs["min"] = self._min_mem_mb
            if self._max_mem_mb:
                self.fields["current_memory_mb"].validators.append(
                    MaxValueValidator(self._max_mem_mb, message=_("Must be ≤ %(limit)s MB"))
                )
                self.fields["current_memory_mb"].widget.attrs["max"] = self._max_mem_mb

            def _range_txt(minv, maxv, unit):
                if minv and maxv:
                    return _("Range: %(min)s–%(max)s %(u)s (flavor limits).") % {"min": minv, "max": maxv, "u": unit}
                if maxv:
                    return _("Up to %(max)s %(u)s (flavor limit).") % {"max": maxv, "u": unit}
                if minv:
                    return _("At least %(min)s %(u)s (flavor minimum).") % {"min": minv, "u": unit}
                return ""

            txt_v = _range_txt(self._min_vcpus, self._max_vcpus, "vCPUs")
            txt_m = _range_txt(self._min_mem_mb, self._max_mem_mb, "MB")
            if txt_v:
                self.fields["current_vcpus"].help_text = txt_v
            if txt_m:
                self.fields["current_memory_mb"].help_text = txt_m

        except Exception:
            LOG.exception("Could not resolve flavor limits for %s", inst_id)

    def clean(self):
        cleaned = super().clean()
        v = cleaned.get("current_vcpus")
        m = cleaned.get("current_memory_mb")

        if v is None and m is None:
            raise forms.ValidationError(_("Provide vCPUs and/or memory."))

        if not cleaned.get("instance_id"):
            raise forms.ValidationError(_("Internal error: missing instance id."))

        errors = {}
        if v is not None:
            if self._min_vcpus and v < self._min_vcpus:
                errors["current_vcpus"] = _("vCPUs cannot be less than flavor minimum (%(min)s).") % {
                    "min": self._min_vcpus}
            if self._max_vcpus and v > self._max_vcpus:
                errors["current_vcpus"] = _("Cannot exceed flavor vCPUs (%(max)s).") % {"max": self._max_vcpus}

        if m is not None:
            if self._min_mem_mb and m < self._min_mem_mb:
                errors["current_memory_mb"] = _("Memory cannot be less than flavor minimum (%(min)s MB).") % {
                    "min": self._min_mem_mb}
            if self._max_mem_mb and m > self._max_mem_mb:
                errors["current_memory_mb"] = _("Cannot exceed flavor memory (%(max)s MB).") % {
                    "max": self._max_mem_mb}

        if errors:
            for field, msg in errors.items():
                self.add_error(field, msg)
            raise forms.ValidationError(_("One or more fields are out of allowed range."))

        return cleaned

    def handle(self, request, data):
        payload = {
            k: v for k, v in {
                "current_vcpus": data.get("current_vcpus"),
                "current_memory_mb": data.get("current_memory_mb"),
                "persist": bool(data.get("persist")),
            }.items() if v is not None
        }

        try:
            sess = api_keystone.keystoneclient(request).session
            base = api_base.url_for(request, 'compute')
            if not base:
                raise RuntimeError("Could not resolve Nova endpoint")

            url = f"{base.rstrip('/')}/os-xloud-adjust/{data['instance_id']}"
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                # "X-OpenStack-Nova-API-Version": "2.93",
            }

            LOG.info("XLoud adjust POST %s payload=%s", url, payload)
            resp = sess.post(url, json=payload, headers=headers)
            LOG.info("XLoud adjust -> %s %s", resp.status_code, (resp.text or "")[:300])

            if resp.status_code in (200, 202, 204):
                messages.success(request, _("Adjust request accepted."))
                return True

            self.api_error(
                _("Adjust failed (%(code)s): %(body)s") % {
                    "code": resp.status_code,
                    "body": (resp.text or _("No response body"))[:500],
                }
            )
            return False

        except forms.ValidationError:
            raise
        except Exception as e:
            LOG.exception("Adjust failed with unexpected error")
            self.api_error(_("Adjust failed: %s") % e)
            return False

####################################################################################################################