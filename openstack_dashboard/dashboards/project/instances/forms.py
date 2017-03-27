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

from django.core.urlresolvers import reverse
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables

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

    def __init__(self, request, *args, **kwargs):
        super(RebuildInstanceForm, self).__init__(request, *args, **kwargs)
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
        try:
            api.nova.server_rebuild(request, instance, image, password,
                                    disk_config)
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

    def __init__(self, *args, **kwargs):
        super(AttachVolume, self).__init__(*args, **kwargs)

        # Populate volume choices
        volume_list = kwargs.get('initial', {}).get("volume_list", [])
        volumes = []
        for volume in volume_list:
            # Only show volumes that aren't attached to an instance already
            if not volume.attachments:
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
        except Exception:
            redirect = reverse('horizon:project:instances:index')
            exceptions.handle(request,
                              _('Unable to attach volume.'),
                              redirect=redirect)
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
        except Exception:
            redirect = reverse('horizon:project:instances:index')
            exceptions.handle(request,
                              _("Unable to detach volume."),
                              redirect=redirect)
        return True


class AttachInterface(forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())
    network = forms.ThemableChoiceField(label=_("Network"))

    def __init__(self, request, *args, **kwargs):
        super(AttachInterface, self).__init__(request, *args, **kwargs)
        networks = instance_utils.network_field_data(request,
                                                     include_empty_option=True)
        self.fields['network'].choices = networks

    def handle(self, request, data):
        instance_id = data['instance_id']
        network = data.get('network')
        try:
            api.nova.interface_attach(request, instance_id, net_id=network)
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
