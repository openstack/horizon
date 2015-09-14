# Copyright 2012 Nebula, Inc.
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

import re

import netaddr
import six

from django.core.exceptions import ValidationError  # noqa
from django.core import urlresolvers
from django.forms import fields
from django.forms.utils import flatatt  # noqa
from django.forms import widgets
from django.utils.encoding import force_text
from django.utils.functional import Promise  # noqa
from django.utils import html
from django.utils.translation import ugettext_lazy as _

ip_allowed_symbols_re = re.compile(r'^[a-fA-F0-9:/\.]+$')
IPv4 = 1
IPv6 = 2


class IPField(fields.Field):
    """Form field for entering IP/range values, with validation.
    Supports IPv4/IPv6 in the format:
    .. xxx.xxx.xxx.xxx
    .. xxx.xxx.xxx.xxx/zz
    .. ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff
    .. ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/zz
    and all compressed forms. Also the short forms
    are supported:
    xxx/yy
    xxx.xxx/yy

    .. attribute:: version

        Specifies which IP version to validate,
        valid values are 1 (fields.IPv4), 2 (fields.IPv6) or
        both - 3 (fields.IPv4 | fields.IPv6).
        Defaults to IPv4 (1)

    .. attribute:: mask

        Boolean flag to validate subnet masks along with IP address.
        E.g: 10.0.0.1/32

    .. attribute:: mask_range_from
        Subnet range limitation, e.g. 16
        That means the input mask will be checked to be in the range
        16:max_value. Useful to limit the subnet ranges
        to A/B/C-class networks.
    """
    invalid_format_message = _("Incorrect format for IP address")
    invalid_version_message = _("Invalid version for IP address")
    invalid_mask_message = _("Invalid subnet mask")
    max_v4_mask = 32
    max_v6_mask = 128

    def __init__(self, *args, **kwargs):
        self.mask = kwargs.pop("mask", None)
        self.min_mask = kwargs.pop("mask_range_from", 0)
        self.version = kwargs.pop('version', IPv4)

        super(IPField, self).__init__(*args, **kwargs)

    def validate(self, value):
        super(IPField, self).validate(value)
        if not value and not self.required:
            return

        try:
            if self.mask:
                self.ip = netaddr.IPNetwork(value)
            else:
                self.ip = netaddr.IPAddress(value)
        except Exception:
            raise ValidationError(self.invalid_format_message)

        if not any([self.version & IPv4 > 0 and self.ip.version == 4,
                    self.version & IPv6 > 0 and self.ip.version == 6]):
            raise ValidationError(self.invalid_version_message)

        if self.mask:
            if self.ip.version == 4 and \
                    not self.min_mask <= self.ip.prefixlen <= self.max_v4_mask:
                raise ValidationError(self.invalid_mask_message)

            if self.ip.version == 6 and \
                    not self.min_mask <= self.ip.prefixlen <= self.max_v6_mask:
                raise ValidationError(self.invalid_mask_message)

    def clean(self, value):
        super(IPField, self).clean(value)
        return str(getattr(self, "ip", ""))


class MultiIPField(IPField):
    """Extends IPField to allow comma-separated lists of addresses."""
    def validate(self, value):
        self.addresses = []
        if value:
            addresses = value.split(',')
            for ip in addresses:
                super(MultiIPField, self).validate(ip)
                self.addresses.append(ip)
        else:
            super(MultiIPField, self).validate(value)

    def clean(self, value):
        super(MultiIPField, self).clean(value)
        return str(','.join(getattr(self, "addresses", [])))


class SelectWidget(widgets.Select):
    """Customizable select widget, that allows to render
    data-xxx attributes from choices. This widget also
    allows user to specify additional html attributes
    for choices.

    .. attribute:: data_attrs

        Specifies object properties to serialize as
        data-xxx attribute. If passed ('id', ),
        this will be rendered as:
        <option data-id="123">option_value</option>
        where 123 is the value of choice_value.id

    .. attribute:: transform

        A callable used to render the display value
        from the option object.

    .. attribute:: transform_html_attrs

        A callable used to render additional HTML attributes
        for the option object. It returns a dictionary
        containing the html attributes and their values.
        For example, to define a title attribute for the
        choices::

            helpText = { 'Apple': 'This is a fruit',
                      'Carrot': 'This is a vegetable' }

            def get_title(data):
                text = helpText.get(data, None)
                if text:
                    return {'title': text}
                else:
                    return {}

            ....
            ....

            widget=forms.SelectWidget( attrs={'class': 'switchable',
                                             'data-slug': 'source'},
                                    transform_html_attrs=get_title )

            self.fields[<field name>].choices =
                ([
                    ('apple','Apple'),
                    ('carrot','Carrot')
                ])

    """
    def __init__(self, attrs=None, choices=(), data_attrs=(), transform=None,
                 transform_html_attrs=None):
        self.data_attrs = data_attrs
        self.transform = transform
        self.transform_html_attrs = transform_html_attrs
        super(SelectWidget, self).__init__(attrs, choices)

    def render_option(self, selected_choices, option_value, option_label):
        option_value = force_text(option_value)
        other_html = (u' selected="selected"'
                      if option_value in selected_choices else '')

        if callable(self.transform_html_attrs):
            html_attrs = self.transform_html_attrs(option_label)
            other_html += flatatt(html_attrs)

        if not isinstance(option_label, (six.string_types, Promise)):
            for data_attr in self.data_attrs:
                data_value = html.conditional_escape(
                    force_text(getattr(option_label,
                                       data_attr, "")))
                other_html += ' data-%s="%s"' % (data_attr, data_value)

            if callable(self.transform):
                option_label = self.transform(option_label)

        return u'<option value="%s"%s>%s</option>' % (
            html.escape(option_value), other_html,
            html.conditional_escape(force_text(option_label)))


class DynamicSelectWidget(widgets.Select):
    """A subclass of the ``Select`` widget which renders extra attributes for
    use in callbacks to handle dynamic changes to the available choices.
    """
    _data_add_url_attr = "data-add-item-url"

    def render(self, *args, **kwargs):
        add_item_url = self.get_add_item_url()
        if add_item_url is not None:
            self.attrs[self._data_add_url_attr] = add_item_url
        return super(DynamicSelectWidget, self).render(*args, **kwargs)

    def get_add_item_url(self):
        if callable(self.add_item_link):
            return self.add_item_link()
        try:
            if self.add_item_link_args:
                return urlresolvers.reverse(self.add_item_link,
                                            args=self.add_item_link_args)
            else:
                return urlresolvers.reverse(self.add_item_link)
        except urlresolvers.NoReverseMatch:
            return self.add_item_link


class DynamicChoiceField(fields.ChoiceField):
    """A subclass of ``ChoiceField`` with additional properties that make
    dynamically updating its elements easier.

    Notably, the field declaration takes an extra argument, ``add_item_link``
    which may be a string or callable defining the URL that should be used
    for the "add" link associated with the field.
    """
    widget = DynamicSelectWidget

    def __init__(self,
                 add_item_link=None,
                 add_item_link_args=None,
                 *args,
                 **kwargs):
        super(DynamicChoiceField, self).__init__(*args, **kwargs)
        self.widget.add_item_link = add_item_link
        self.widget.add_item_link_args = add_item_link_args


class DynamicTypedChoiceField(DynamicChoiceField, fields.TypedChoiceField):
    """Simple mix of ``DynamicChoiceField`` and ``TypedChoiceField``."""
    pass
