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

from django.template.defaultfilters import filesizeformat
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables
import six

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import validators

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.images \
    import utils as image_utils
from openstack_dashboard.dashboards.project.instances \
    import utils as instance_utils


def _image_choice_title(img):
    gb = filesizeformat(img.size)
    return '%s (%s)' % (img.name or img.id, gb)


class RebuildInstanceForm(forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())

    image = forms.ChoiceField(
        label=_("Select Image"),
        widget=forms.ThemableSelectWidget(
            attrs={'class': 'image-selector'},
            data_attrs=('size', 'display-name'),
            transform=_image_choice_title))
    password = forms.RegexField(
        label=_("Rebuild Password"),
        required=False,
        widget=forms.PasswordInput(render_value=False),
        regex=validators.password_validator(),
        error_messages={'invalid': validators.password_validator_msg()})
    confirm_password = forms.CharField(
        label=_("Confirm Rebuild Password"),
        required=False,
        widget=forms.PasswordInput(render_value=False))
    disk_config = forms.ThemableChoiceField(label=_("Disk Partition"),
                                            required=False)
    description = forms.CharField(
        label=_("Description"),
        widget=forms.Textarea(attrs={'rows': 4}),
        max_length=255,
        required=False
    )

    def __init__(self, request, *args, **kwargs):
        super(RebuildInstanceForm, self).__init__(request, *args, **kwargs)
        if not api.nova.is_feature_available(request, "instance_description"):
            del self.fields['description']
        instance_id = kwargs.get('initial', {}).get('instance_id')
        self.fields['instance_id'].initial = instance_id

        images = image_utils.get_available_images(request,
                                                  request.user.tenant_id)
        choices = [(image.id, image) for image in images]
        if choices:
            choices.insert(0, ("", _("Select Image")))
        else:
            choices.insert(0, ("", _("No images available")))
        self.fields['image'].choices = choices

        if not api.nova.can_set_server_password():
            del self.fields['password']
            del self.fields['confirm_password']

        try:
            if not api.nova.extension_supported("DiskConfig", request):
                del self.fields['disk_config']
            else:
                # Set our disk_config choices
                config_choices = [("AUTO", _("Automatic")),
                                  ("MANUAL", _("Manual"))]
                self.fields['disk_config'].choices = config_choices
        except Exception:
            exceptions.handle(request, _('Unable to retrieve extensions '
                                         'information.'))

    def clean(self):
        cleaned_data = super(RebuildInstanceForm, self).clean()
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
            api.nova.server_rebuild(request, instance, image, password,
                                    disk_config, description=description)
            messages.info(request, _('Rebuilding instance %s.') % instance)
        except Exception:
            redirect = reverse('horizon:project:instances:index')
            exceptions.handle(request, _("Unable to rebuild instance."),
                              redirect=redirect)
        return True


class DecryptPasswordInstanceForm(forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())
    _keypair_name_label = _("Key Pair Name")
    _keypair_name_help = _("The Key Pair name that "
                           "was associated with the instance")
    _attrs = {'readonly': 'readonly', 'rows': 4}
    keypair_name = forms.CharField(widget=forms.widgets.TextInput(_attrs),
                                   label=_keypair_name_label,
                                   help_text=_keypair_name_help,
                                   required=False)
    _encrypted_pwd_help = _("The instance password encrypted "
                            "with your public key.")
    encrypted_password = forms.CharField(widget=forms.widgets.Textarea(_attrs),
                                         label=_("Encrypted Password"),
                                         help_text=_encrypted_pwd_help,
                                         required=False)

    def __init__(self, request, *args, **kwargs):
        super(DecryptPasswordInstanceForm, self).__init__(request,
                                                          *args,
                                                          **kwargs)
        instance_id = kwargs.get('initial', {}).get('instance_id')
        self.fields['instance_id'].initial = instance_id
        keypair_name = kwargs.get('initial', {}).get('keypair_name')
        self.fields['keypair_name'].initial = keypair_name
        try:
            result = api.nova.get_password(request, instance_id)
            if not result:
                _unavailable = _("Instance Password is not set"
                                 " or is not yet available")
                self.fields['encrypted_password'].initial = _unavailable
            else:
                self.fields['encrypted_password'].initial = result
                self.fields['private_key_file'] = forms.FileField(
                    label=_('Private Key File'),
                    widget=forms.FileInput())
                self.fields['private_key'] = forms.CharField(
                    widget=forms.widgets.Textarea(),
                    label=_("OR Copy/Paste your Private Key"))
                _attrs = {'readonly': 'readonly'}
                self.fields['decrypted_password'] = forms.CharField(
                    widget=forms.widgets.TextInput(_attrs),
                    label=_("Password"),
                    required=False)
        except Exception:
            redirect = reverse('horizon:project:instances:index')
            _error = _("Unable to retrieve instance password.")
            exceptions.handle(request, _error, redirect=redirect)

    def handle(self, request, data):
        return True


class AttachVolume(forms.SelfHandlingForm):
    volume = forms.ChoiceField(label=_("Volume ID"),
                               widget=forms.ThemableSelectWidget(),
                               help_text=_("Select a volume to attach "
                                           "to this instance."))
    device = forms.CharField(label=_("Device Name"),
                             widget=forms.HiddenInput(),
                             required=False,
                             help_text=_("Actual device name may differ due "
                                         "to hypervisor settings. If not "
                                         "specified, then hypervisor will "
                                         "select a device name."))
    instance_id = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, request, *args, **kwargs):
        super(AttachVolume, self).__init__(request, *args, **kwargs)

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
                    (volume.id, '%(name)s (%(id)s)'
                     % {"name": volume.name, "id": volume.id}))
        if volumes:
            volumes.insert(0, ("", _("Select a volume")))
        else:
            volumes.insert(0, ("", _("No volumes available")))
        self.fields['volume'].choices = volumes

    def handle(self, request, data):
        instance_id = self.initial.get("instance_id", None)
        volume_choices = dict(self.fields['volume'].choices)
        volume = volume_choices.get(data['volume'],
                                    _("Unknown volume (None)"))
        volume_id = data.get('volume')

        device = data.get('device') or None

        try:
            attach = api.nova.instance_volume_attach(request,
                                                     volume_id,
                                                     instance_id,
                                                     device)

            message = _('Attaching volume %(vol)s to instance '
                        '%(inst)s on %(dev)s.') % {"vol": volume,
                                                   "inst": instance_id,
                                                   "dev": attach.device}
            messages.info(request, message)
        except Exception as ex:
            redirect = reverse('horizon:project:instances:index')
            if isinstance(ex, api.nova.VolumeMultiattachNotSupported):
                # Use the specific error from the specific message.
                msg = six.text_type(ex)
            else:
                # Use a generic error message.
                msg = _('Unable to attach volume: %s') % ex
            exceptions.handle(request, msg, redirect=redirect)
        return True


class DetachVolume(forms.SelfHandlingForm):
    volume = forms.ChoiceField(label=_("Volume ID"),
                               widget=forms.ThemableSelectWidget(),
                               help_text=_("Select a volume to detach "
                                           "from this instance."))
    instance_id = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(DetachVolume, self).__init__(*args, **kwargs)

        # Populate instance id
        instance_id = kwargs.get('initial', {}).get("instance_id", None)

        # Populate attached volumes
        try:
            volumes = []
            volume_list = api.nova.instance_volumes_list(self.request,
                                                         instance_id)
            for volume in volume_list:
                volumes.append((volume.id, '%s (%s)' % (volume.name,
                                                        volume.id)))
            if volume_list:
                volumes.insert(0, ("", _("Select a volume")))
            else:
                volumes.insert(0, ("", _("No volumes attached")))

            self.fields['volume'].choices = volumes
        except Exception:
            redirect = reverse('horizon:project:instances:index')
            exceptions.handle(self.request, _("Unable to detach volume."),
                              redirect=redirect)

    def handle(self, request, data):
        instance_id = self.initial.get("instance_id", None)
        volume_choices = dict(self.fields['volume'].choices)
        volume = volume_choices.get(data['volume'],
                                    _("Unknown volume (None)"))
        volume_id = data.get('volume')

        try:
            api.nova.instance_volume_detach(request,
                                            instance_id,
                                            volume_id)

            message = _('Detaching volume %(vol)s from instance '
                        '%(inst)s.') % {"vol": volume,
                                        "inst": instance_id}
            messages.info(request, message)
        except Exception as ex:
            redirect = reverse('horizon:project:instances:index')
            exceptions.handle(
                request, _("Unable to detach volume: %s") % ex,
                redirect=redirect)
        return True


class AttachInterface(forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())
    specification_method = forms.ThemableChoiceField(
        label=_("The way to specify an interface"),
        initial=False,
        widget=forms.ThemableSelectWidget(attrs={
            'class': 'switchable',
            'data-slug': 'specification_method',
        }))
    port = forms.ThemableChoiceField(
        label=_("Port"),
        required=False,
        widget=forms.ThemableSelectWidget(attrs={
            'class': 'switched',
            'data-required-when-shown': 'true',
            'data-switch-on': 'specification_method',
            'data-specification_method-port': _('Port'),
        }))
    network = forms.ThemableChoiceField(
        label=_("Network"),
        required=False,
        widget=forms.ThemableSelectWidget(attrs={
            'class': 'switched',
            'data-required-when-shown': 'true',
            'data-switch-on': 'specification_method',
            'data-specification_method-network': _('Network'),
        }))
    fixed_ip = forms.IPField(
        label=_("Fixed IP Address"),
        required=False,
        help_text=_("IP address for the new port"),
        version=forms.IPv4 | forms.IPv6,
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'specification_method',
            'data-specification_method-network': _('Fixed IP Address'),
        }))

    def __init__(self, request, *args, **kwargs):
        super(AttachInterface, self).__init__(request, *args, **kwargs)
        networks = instance_utils.network_field_data(request,
                                                     include_empty_option=True,
                                                     with_cidr=True)
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
            api.nova.interface_attach(request,
                                      instance_id,
                                      net_id=net_id,
                                      fixed_ip=fixed_ip,
                                      port_id=port_id)
            msg = _('Attaching interface for instance %s.') % instance_id
            messages.success(request, msg)
        except Exception:
            redirect = reverse('horizon:project:instances:index')
            exceptions.handle(request, _("Unable to attach interface."),
                              redirect=redirect)
        return True


class DetachInterface(forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())
    port = forms.ThemableChoiceField(label=_("Port"))

    def __init__(self, request, *args, **kwargs):
        super(DetachInterface, self).__init__(request, *args, **kwargs)
        instance_id = self.initial.get("instance_id", None)

        ports = []
        try:
            ports = api.neutron.port_list(request, device_id=instance_id)
        except Exception:
            exceptions.handle(request, _('Unable to retrieve ports '
                                         'information.'))
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
            msg = _('Detached interface %(port)s for instance '
                    '%(instance)s.') % {'port': port, 'instance': instance_id}
            messages.success(request, msg)
        except Exception:
            redirect = reverse('horizon:project:instances:index')
            exceptions.handle(request, _("Unable to detach interface."),
                              redirect=redirect)
        return True


class Disassociate(forms.SelfHandlingForm):
    fip = forms.ThemableChoiceField(label=_('Floating IP'))
    is_release = forms.BooleanField(label=_('Release Floating IP'),
                                    required=False)

    def __init__(self, request, *args, **kwargs):
        super(Disassociate, self).__init__(request, *args, **kwargs)
        instance_id = self.initial['instance_id']
        targets = api.neutron.floating_ip_target_list_by_instance(
            request, instance_id)

        target_ids = [t.port_id for t in targets]

        self.fips = [fip for fip
                     in api.neutron.tenant_floating_ip_list(request)
                     if fip.port_id in target_ids]

        fip_choices = [(fip.id, fip.ip) for fip in self.fips]
        fip_choices.insert(0, ('', _('Select a floating IP to disassociate')))
        self.fields['fip'].choices = fip_choices
        self.fields['fip'].initial = self.fips[0].id

    def handle(self, request, data):
        redirect = reverse_lazy('horizon:project:instances:index')
        fip_id = data['fip']
        fips = [fip for fip in self.fips if fip.id == fip_id]
        if not fips:
            messages.error(request,
                           _("The specified floating IP no longer exists."))
            raise exceptions.Http302(redirect)
        fip = fips[0]
        try:
            if data['is_release']:
                api.neutron.tenant_floating_ip_release(request, fip_id)
                messages.success(
                    request,
                    _("Successfully disassociated and released "
                      "floating IP %s") % fip.ip)
            else:
                api.neutron.floating_ip_disassociate(request, fip_id)
                messages.success(
                    request,
                    _("Successfully disassociated floating IP %s") % fip.ip)
        except Exception:
            exceptions.handle(
                request,
                _('Unable to disassociate floating IP %s') % fip.ip,
                redirect=redirect)
        return True


class RescueInstanceForm(forms.SelfHandlingForm):
    image = forms.ChoiceField(
        label=_("Select Image"),
        widget=forms.ThemableSelectWidget(
            attrs={'class': 'image-selector'},
            data_attrs=('size', 'display-name'),
            transform=_image_choice_title))
    password = forms.CharField(label=_("Password"), max_length=255,
                               required=False,
                               widget=forms.PasswordInput(render_value=False))
    failure_url = 'horizon:project:instances:index'

    def __init__(self, request, *args, **kwargs):
        super(RescueInstanceForm, self).__init__(request, *args, **kwargs)
        images = image_utils.get_available_images(request,
                                                  request.user.tenant_id)
        choices = [(image.id, image) for image in images]
        if not choices:
            choices.insert(0, ("", _("No images available")))
        self.fields['image'].choices = choices

    def handle(self, request, data):
        try:
            api.nova.server_rescue(request, self.initial["instance_id"],
                                   password=data["password"],
                                   image=data["image"])
            messages.success(request,
                             _('Successfully rescued instance'))
            return True
        except Exception:
            redirect = reverse(self.failure_url)
            exceptions.handle(request,
                              _('Unable to rescue instance'),
                              redirect=redirect)
