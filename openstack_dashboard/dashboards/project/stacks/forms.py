# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
import re

from django.utils.translation import ugettext_lazy as _  # noqa
from django.views.decorators.debug import sensitive_variables  # noqa

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api

LOG = logging.getLogger(__name__)


def exception_to_validation_msg(e):
    '''
    Extracts a validation message to display to the user.
    '''
    try:
        error = json.loads(str(e))
        # NOTE(jianingy): if no message exists, we just return 'None'
        # and let the caller to deciede what to show
        return error['error'].get('message', None)
    except Exception:
        # NOTE(jianingy): fallback to legacy message parsing approach
        # either if error message isn't a json nor the json isn't in
        # valid format.
        validation_patterns = [
            "Remote error: \w* {'Error': '(.*?)'}",
            'Remote error: \w* (.*?) \[',
            '400 Bad Request\n\nThe server could not comply with the request '
            'since it is either malformed or otherwise incorrect.\n\n (.*)',
            '(ParserError: .*)'
        ]

        for pattern in validation_patterns:
            match = re.search(pattern, str(e))
            if match:
                return match.group(1)


class TemplateForm(forms.SelfHandlingForm):

    class Meta:
        name = _('Select Template')
        help_text = _('From here you can select a template to launch '
                      'a stack.')

    template_source = forms.ChoiceField(label=_('Template Source'),
                                        choices=[('url', _('URL')),
                                                 ('file', _('File')),
                                                 ('raw', _('Direct Input'))],
                                        widget=forms.Select(attrs={
                                            'class': 'switchable',
                                            'data-slug': 'source'}))
    template_upload = forms.FileField(
        label=_('Template File'),
        help_text=_('A local template to upload.'),
        widget=forms.FileInput(attrs={'class': 'switched',
                                      'data-switch-on': 'source',
                                      'data-source-file': _('Template File')}),
        required=False)
    template_url = forms.URLField(
        label=_('Template URL'),
        help_text=_('An external (HTTP) URL to load the template from.'),
        widget=forms.TextInput(attrs={'class': 'switched',
                                      'data-switch-on': 'source',
                                      'data-source-url': _('Template URL')}),
        required=False)
    template_data = forms.CharField(
        label=_('Template Data'),
        help_text=_('The raw contents of the template.'),
        widget=forms.widgets.Textarea(attrs={
                                      'class': 'switched',
                                      'data-switch-on': 'source',
                                      'data-source-raw': _('Template Data')}),
        required=False)

    def __init__(self, *args, **kwargs):
        self.next_view = kwargs.pop('next_view')
        super(TemplateForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned = super(TemplateForm, self).clean()
        template_url = cleaned.get('template_url')
        template_data = cleaned.get('template_data')
        files = self.request.FILES
        has_upload = 'template_upload' in files

        # Uploaded file handler
        if has_upload and not template_url:
            log_template_name = self.request.FILES['template_upload'].name
            LOG.info('got upload %s' % log_template_name)

            tpl = self.request.FILES['template_upload'].read()
            if tpl.startswith('{'):
                try:
                    json.loads(tpl)
                except Exception as e:
                    msg = _('There was a problem parsing the template: %s') % e
                    raise forms.ValidationError(msg)
            cleaned['template_data'] = tpl

        # URL handler
        elif template_url and (has_upload or template_data):
            msg = _('Please specify a template using only one source method.')
            raise forms.ValidationError(msg)

        # Check for raw template input
        elif not template_url and not template_data:
            msg = _('You must specify a template via one of the '
                    'available sources.')
            raise forms.ValidationError(msg)

        # Validate the template and get back the params.
        kwargs = {}
        if cleaned['template_data']:
            kwargs['template'] = cleaned['template_data']
        else:
            kwargs['template_url'] = cleaned['template_url']

        try:
            validated = api.heat.template_validate(self.request, **kwargs)
            cleaned['template_validate'] = validated
        except Exception as e:
            msg = exception_to_validation_msg(e)
            if not msg:
                msg = _('An unknown problem occurred validating the template.')
                LOG.exception(msg)
            raise forms.ValidationError(msg)

        return cleaned

    def handle(self, request, data):
        kwargs = {'parameters': data['template_validate'],
                  'template_data': data['template_data'],
                  'template_url': data['template_url']}
        # NOTE (gabriel): This is a bit of a hack, essentially rewriting this
        # request so that we can chain it as an input to the next view...
        # but hey, it totally works.
        request.method = 'GET'
        return self.next_view.as_view()(request, **kwargs)


class StackCreateForm(forms.SelfHandlingForm):

    param_prefix = '__param_'

    class Meta:
        name = _('Create Stack')

    template_data = forms.CharField(
        widget=forms.widgets.HiddenInput,
        required=False)
    template_url = forms.CharField(
        widget=forms.widgets.HiddenInput,
        required=False)
    parameters = forms.CharField(
        widget=forms.widgets.HiddenInput,
        required=True)
    stack_name = forms.CharField(
        max_length='255',
        label=_('Stack Name'),
        help_text=_('Name of the stack to create.'),
        required=True)
    timeout_mins = forms.IntegerField(
        initial=60,
        label=_('Creation Timeout (minutes)'),
        help_text=_('Stack creation timeout in minutes.'),
        required=True)
    enable_rollback = forms.BooleanField(
        label=_('Rollback On Failure'),
        help_text=_('Enable rollback on create/update failure.'),
        required=False)

    def __init__(self, *args, **kwargs):
        parameters = kwargs.pop('parameters')
        super(StackCreateForm, self).__init__(*args, **kwargs)
        self._build_parameter_fields(parameters)

    def _build_parameter_fields(self, template_validate):

        self.fields['password'] = forms.CharField(
            label=_('Password for user "%s"') % self.request.user.username,
            help_text=_('This is required for operations to be performed '
                        'throughout the lifecycle of the stack'),
            required=True,
            widget=forms.PasswordInput())

        self.help_text = template_validate['Description']

        params = template_validate.get('Parameters', {})

        for param_key, param in params.items():
            field_key = self.param_prefix + param_key
            field_args = {
                'initial': param.get('Default', None),
                'label': param_key,
                'help_text': param.get('Description', ''),
                'required': param.get('Default', None) is None
            }

            param_type = param.get('Type', None)

            if 'AllowedValues' in param:
                choices = map(lambda x: (x, x), param['AllowedValues'])
                field_args['choices'] = choices
                field = forms.ChoiceField(**field_args)

            elif param_type in ('CommaDelimitedList', 'String'):
                if 'MinLength' in param:
                    field_args['min_length'] = int(param['MinLength'])
                    field_args['required'] = param.get('MinLength', 0) > 0
                if 'MaxLength' in param:
                    field_args['max_length'] = int(param['MaxLength'])
                field = forms.CharField(**field_args)

            elif param_type == 'Number':
                if 'MinValue' in param:
                    field_args['min_value'] = int(param['MinValue'])
                if 'MaxValue' in param:
                    field_args['max_value'] = int(param['MaxValue'])
                field = forms.IntegerField(**field_args)

            self.fields[field_key] = field

    @sensitive_variables('password')
    def handle(self, request, data):
        prefix_length = len(self.param_prefix)
        params_list = [(k[prefix_length:], v) for (k, v) in data.iteritems()
                       if k.startswith(self.param_prefix)]
        fields = {
            'stack_name': data.get('stack_name'),
            'timeout_mins': data.get('timeout_mins'),
            'disable_rollback': not(data.get('enable_rollback')),
            'parameters': dict(params_list),
            'password': data.get('password')
        }

        if data.get('template_data'):
            fields['template'] = data.get('template_data')
        else:
            fields['template_url'] = data.get('template_url')

        try:
            api.heat.stack_create(self.request, **fields)
            messages.success(request, _("Stack creation started."))
            return True
        except Exception as e:
            msg = exception_to_validation_msg(e)
            exceptions.handle(request, msg or _('Stack creation failed.'))
