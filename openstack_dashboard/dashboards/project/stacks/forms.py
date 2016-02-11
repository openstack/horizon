# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json
import logging

import django
from django.conf import settings
from django.utils import html
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables  # noqa

from oslo_utils import strutils
import six

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.images \
    import utils as image_utils
from openstack_dashboard.dashboards.project.instances \
    import utils as instance_utils


LOG = logging.getLogger(__name__)


def create_upload_form_attributes(prefix, input_type, name):
    """Creates attribute dicts for the switchable upload form

    :type prefix: str
    :param prefix: prefix (environment, template) of field
    :type input_type: str
    :param input_type: field type (file, raw, url)
    :type name: str
    :param name: translated text label to display to user
    :rtype: dict
    :return: an attribute set to pass to form build
    """
    attributes = {'class': 'switched', 'data-switch-on': prefix + 'source'}
    attributes['data-' + prefix + 'source-' + input_type] = name
    return attributes


class TemplateForm(forms.SelfHandlingForm):

    class Meta(object):
        name = _('Select Template')
        help_text = _('Select a template to launch a stack.')

    # TODO(jomara) - update URL choice for template & environment files
    # w/ client side download when applicable
    base_choices = [('file', _('File')),
                    ('raw', _('Direct Input'))]
    url_choice = [('url', _('URL'))]
    attributes = {'class': 'switchable', 'data-slug': 'templatesource'}
    template_source = forms.ChoiceField(label=_('Template Source'),
                                        choices=base_choices + url_choice,
                                        widget=forms.Select(attrs=attributes))

    attributes = create_upload_form_attributes(
        'template',
        'file',
        _('Template File'))
    template_upload = forms.FileField(
        label=_('Template File'),
        help_text=_('A local template to upload.'),
        widget=forms.FileInput(attrs=attributes),
        required=False)

    attributes = create_upload_form_attributes(
        'template',
        'url',
        _('Template URL'))
    template_url = forms.URLField(
        label=_('Template URL'),
        help_text=_('An external (HTTP) URL to load the template from.'),
        widget=forms.TextInput(attrs=attributes),
        required=False)

    attributes = create_upload_form_attributes(
        'template',
        'raw',
        _('Template Data'))
    template_data = forms.CharField(
        label=_('Template Data'),
        help_text=_('The raw contents of the template.'),
        widget=forms.widgets.Textarea(attrs=attributes),
        required=False)

    attributes = {'data-slug': 'envsource', 'class': 'switchable'}
    environment_source = forms.ChoiceField(
        label=_('Environment Source'),
        choices=base_choices,
        widget=forms.Select(attrs=attributes),
        required=False)

    attributes = create_upload_form_attributes(
        'env',
        'file',
        _('Environment File'))
    environment_upload = forms.FileField(
        label=_('Environment File'),
        help_text=_('A local environment to upload.'),
        widget=forms.FileInput(attrs=attributes),
        required=False)

    attributes = create_upload_form_attributes(
        'env',
        'raw',
        _('Environment Data'))
    environment_data = forms.CharField(
        label=_('Environment Data'),
        help_text=_('The raw contents of the environment file.'),
        widget=forms.widgets.Textarea(attrs=attributes),
        required=False)

    if django.VERSION >= (1, 9):
        # Note(Itxaka): On django>=1.9 Charfield has an strip option that
        # we need to set to False as to not hit
        # https://bugs.launchpad.net/python-heatclient/+bug/1546166
        environment_data.strip = False
        template_data.strip = False

    def __init__(self, *args, **kwargs):
        self.next_view = kwargs.pop('next_view')
        super(TemplateForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned = super(TemplateForm, self).clean()

        files = self.request.FILES
        self.clean_uploaded_files('template', _('template'), cleaned, files)
        self.clean_uploaded_files('environment', _('environment'), cleaned,
                                  files)

        # Validate the template and get back the params.
        kwargs = {}
        if cleaned['environment_data']:
            kwargs['environment'] = cleaned['environment_data']
        try:
            files, tpl =\
                api.heat.get_template_files(cleaned.get('template_data'),
                                            cleaned.get('template_url'))
            kwargs['files'] = files
            kwargs['template'] = tpl
            validated = api.heat.template_validate(self.request, **kwargs)
            cleaned['template_validate'] = validated
            cleaned['template_validate']['files'] = files
            cleaned['template_validate']['template'] = tpl
        except Exception as e:
            raise forms.ValidationError(six.text_type(e))

        return cleaned

    def clean_uploaded_files(self, prefix, field_label, cleaned, files):
        """Cleans Template & Environment data from form upload.

        Does some of the crunchy bits for processing uploads vs raw
        data depending on what the user specified. Identical process
        for environment data & template data.

        :type prefix: str
        :param prefix: prefix (environment, template) of field
        :type field_label: str
        :param field_label: translated prefix str for messages
        :type input_type: dict
        :param prefix: existing cleaned fields from form
        :rtype: dict
        :return: cleaned dict including environment & template data
        """

        upload_str = prefix + "_upload"
        data_str = prefix + "_data"
        url = cleaned.get(prefix + '_url')
        data = cleaned.get(prefix + '_data')

        has_upload = upload_str in files
        # Uploaded file handler
        if has_upload and not url:
            log_template_name = files[upload_str].name
            LOG.info('got upload %s' % log_template_name)

            tpl = files[upload_str].read()
            if tpl.startswith('{'):
                try:
                    json.loads(tpl)
                except Exception as e:
                    msg = _('There was a problem parsing the'
                            ' %(prefix)s: %(error)s')
                    msg = msg % {'prefix': prefix, 'error': six.text_type(e)}
                    raise forms.ValidationError(msg)
            cleaned[data_str] = tpl

        # URL handler
        elif url and (has_upload or data):
            msg = _('Please specify a %s using only one source method.')
            msg = msg % field_label
            raise forms.ValidationError(msg)

        elif prefix == 'template':
            # Check for raw template input - blank environment allowed
            if not url and not data:
                msg = _('You must specify a template via one of the '
                        'available sources.')
                raise forms.ValidationError(msg)

    def create_kwargs(self, data):
        kwargs = {'parameters': data['template_validate'],
                  'environment_data': data['environment_data']}
        if data.get('stack_id'):
            kwargs['stack_id'] = data['stack_id']
        return kwargs

    def handle(self, request, data):
        kwargs = self.create_kwargs(data)
        # NOTE (gabriel): This is a bit of a hack, essentially rewriting this
        # request so that we can chain it as an input to the next view...
        # but hey, it totally works.
        request.method = 'GET'

        return self.next_view.as_view()(request, **kwargs)


class ChangeTemplateForm(TemplateForm):
    class Meta(object):
        name = _('Edit Template')
        help_text = _('Select a new template to re-launch a stack.')
    stack_id = forms.CharField(label=_('Stack ID'),
                               widget=forms.widgets.HiddenInput)
    stack_name = forms.CharField(label=_('Stack Name'),
                                 widget=forms.TextInput(attrs={'readonly':
                                                               'readonly'}))


class PreviewTemplateForm(TemplateForm):
    class Meta(object):
        name = _('Preview Template')
        help_text = _('Select a new template to preview a stack.')


class CreateStackForm(forms.SelfHandlingForm):

    param_prefix = '__param_'

    class Meta(object):
        name = _('Create Stack')

    environment_data = forms.CharField(
        widget=forms.widgets.HiddenInput,
        required=False)
    if django.VERSION >= (1, 9):
        # Note(Itxaka): On django>=1.9 Charfield has an strip option that
        # we need to set to False as to not hit
        # https://bugs.launchpad.net/python-heatclient/+bug/1546166
        environment_data.strip = False

    parameters = forms.CharField(
        widget=forms.widgets.HiddenInput)
    stack_name = forms.RegexField(
        max_length=255,
        label=_('Stack Name'),
        help_text=_('Name of the stack to create.'),
        regex=r"^[a-zA-Z][a-zA-Z0-9_.-]*$",
        error_messages={'invalid':
                        _('Name must start with a letter and may '
                          'only contain letters, numbers, underscores, '
                          'periods and hyphens.')})
    timeout_mins = forms.IntegerField(
        initial=60,
        label=_('Creation Timeout (minutes)'),
        help_text=_('Stack creation timeout in minutes.'))
    enable_rollback = forms.BooleanField(
        label=_('Rollback On Failure'),
        help_text=_('Enable rollback on create/update failure.'),
        required=False)

    def __init__(self, *args, **kwargs):
        parameters = kwargs.pop('parameters')
        # special case: load template data from API, not passed in params
        if kwargs.get('validate_me'):
            parameters = kwargs.pop('validate_me')
        super(CreateStackForm, self).__init__(*args, **kwargs)

        if self._stack_password_enabled():
            self.fields['password'] = forms.CharField(
                label=_('Password for user "%s"') % self.request.user.username,
                help_text=_('This is required for operations to be performed '
                            'throughout the lifecycle of the stack'),
                widget=forms.PasswordInput())

        self._build_parameter_fields(parameters)

    def _stack_password_enabled(self):
        stack_settings = getattr(settings, 'OPENSTACK_HEAT_STACK', {})
        return stack_settings.get('enable_user_pass', True)

    def _build_parameter_fields(self, template_validate):
        self.help_text = template_validate['Description']

        params = template_validate.get('Parameters', {})
        if template_validate.get('ParameterGroups'):
            params_in_order = []
            for group in template_validate['ParameterGroups']:
                for param in group.get('parameters', []):
                    if param in params:
                        params_in_order.append((param, params[param]))
        else:
            # no parameter groups, simply sorted to make the order fixed
            params_in_order = sorted(params.items())
        for param_key, param in params_in_order:
            field = None
            field_key = self.param_prefix + param_key
            field_args = {
                'initial': param.get('Default', None),
                'label': param.get('Label', param_key),
                'help_text': html.escape(param.get('Description', '')),
                'required': param.get('Default', None) is None
            }

            param_type = param.get('Type', None)
            hidden = strutils.bool_from_string(param.get('NoEcho', 'false'))
            if 'CustomConstraint' in param:
                choices = self._populate_custom_choices(
                    param['CustomConstraint'])
                field_args['choices'] = choices
                field = forms.ChoiceField(**field_args)

            elif 'AllowedValues' in param:
                choices = map(lambda x: (x, x), param['AllowedValues'])
                field_args['choices'] = choices
                field = forms.ChoiceField(**field_args)

            elif param_type == 'Json' and 'Default' in param:
                field_args['initial'] = json.dumps(param['Default'])
                field = forms.CharField(**field_args)

            elif param_type in ('CommaDelimitedList', 'String', 'Json'):
                if 'MinLength' in param:
                    field_args['min_length'] = int(param['MinLength'])
                    field_args['required'] = field_args['min_length'] > 0
                if 'MaxLength' in param:
                    field_args['max_length'] = int(param['MaxLength'])
                if hidden:
                    field_args['widget'] = forms.PasswordInput(
                        render_value=True)
                field = forms.CharField(**field_args)

            elif param_type == 'Number':
                if 'MinValue' in param:
                    field_args['min_value'] = int(param['MinValue'])
                if 'MaxValue' in param:
                    field_args['max_value'] = int(param['MaxValue'])
                field = forms.IntegerField(**field_args)

            # heat-api currently returns the boolean type in lowercase
            # (see https://bugs.launchpad.net/heat/+bug/1361448)
            # so for better compatibility both are checked here
            elif param_type in ('Boolean', 'boolean'):
                field_args['required'] = False
                field = forms.BooleanField(**field_args)

            if field:
                self.fields[field_key] = field

    @sensitive_variables('password')
    def handle(self, request, data):
        prefix_length = len(self.param_prefix)
        params_list = [(k[prefix_length:], v) for (k, v) in six.iteritems(data)
                       if k.startswith(self.param_prefix)]
        fields = {
            'stack_name': data.get('stack_name'),
            'timeout_mins': data.get('timeout_mins'),
            'disable_rollback': not(data.get('enable_rollback')),
            'parameters': dict(params_list),
            'files': json.loads(data.get('parameters')).get('files'),
            'template': json.loads(data.get('parameters')).get('template')
        }
        if data.get('password'):
            fields['password'] = data.get('password')

        if data.get('environment_data'):
            fields['environment'] = data.get('environment_data')

        try:
            api.heat.stack_create(self.request, **fields)
            messages.info(request, _("Stack creation started."))
            return True
        except Exception:
            exceptions.handle(request)

    def _populate_custom_choices(self, custom_type):
        if custom_type == 'neutron.network':
            return instance_utils.network_field_data(self.request, True)
        if custom_type == 'nova.keypair':
            return instance_utils.keypair_field_data(self.request, True)
        if custom_type == 'glance.image':
            return image_utils.image_field_data(self.request, True)
        if custom_type == 'nova.flavor':
            return instance_utils.flavor_field_data(self.request, True)
        return []


class EditStackForm(CreateStackForm):

    class Meta(object):
        name = _('Update Stack Parameters')

    stack_id = forms.CharField(
        label=_('Stack ID'),
        widget=forms.widgets.HiddenInput)
    stack_name = forms.CharField(
        label=_('Stack Name'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    @sensitive_variables('password')
    def handle(self, request, data):
        prefix_length = len(self.param_prefix)
        params_list = [(k[prefix_length:], v) for (k, v) in six.iteritems(data)
                       if k.startswith(self.param_prefix)]

        stack_id = data.get('stack_id')
        fields = {
            'stack_name': data.get('stack_name'),
            'timeout_mins': data.get('timeout_mins'),
            'disable_rollback': not(data.get('enable_rollback')),
            'parameters': dict(params_list),
            'files': json.loads(data.get('parameters')).get('files'),
            'template': json.loads(data.get('parameters')).get('template')
        }
        if data.get('password'):
            fields['password'] = data.get('password')

        try:
            api.heat.stack_update(self.request, stack_id=stack_id, **fields)
            messages.info(request, _("Stack update started."))
            return True
        except Exception:
            exceptions.handle(request)


class PreviewStackForm(CreateStackForm):

    class Meta(object):
        name = _('Preview Stack Parameters')

    def __init__(self, *args, **kwargs):
        self.next_view = kwargs.pop('next_view')
        super(CreateStackForm, self).__init__(*args, **kwargs)

    def handle(self, request, data):
        prefix_length = len(self.param_prefix)
        params_list = [(k[prefix_length:], v) for (k, v) in six.iteritems(data)
                       if k.startswith(self.param_prefix)]
        fields = {
            'stack_name': data.get('stack_name'),
            'timeout_mins': data.get('timeout_mins'),
            'disable_rollback': not(data.get('enable_rollback')),
            'parameters': dict(params_list),
            'files': json.loads(data.get('parameters')).get('files'),
            'template': json.loads(data.get('parameters')).get('template')
        }

        if data.get('environment_data'):
            fields['environment'] = data.get('environment_data')

        try:
            stack_preview = api.heat.stack_preview(self.request, **fields)
            request.method = 'GET'
            return self.next_view.as_view()(request,
                                            stack_preview=stack_preview)
        except Exception:
            exceptions.handle(request)
