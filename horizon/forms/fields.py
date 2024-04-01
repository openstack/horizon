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

import collections
import itertools
import re

import netaddr

from oslo_utils import uuidutils

from django.core.exceptions import ValidationError
from django.forms import fields
from django.forms import forms
from django.forms.utils import flatatt
from django.forms import widgets
from django.template.loader import get_template
from django import urls
from django.utils.encoding import force_str
from django.utils.functional import Promise
from django.utils.html import format_html, format_html_join, escape, flatatt
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

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

        super().__init__(*args, **kwargs)

    def validate(self, value):
        super().validate(value)
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
        super().clean(value)
        return str(getattr(self, "ip", ""))


class MultiIPField(IPField):
    """Extends IPField to allow comma-separated lists of addresses."""
    def validate(self, value):
        self.addresses = []
        if value:
            addresses = value.split(',')
            for ip in addresses:
                super().validate(ip)
                self.addresses.append(ip)
        else:
            super().validate(value)

    def clean(self, value):
        super().clean(value)
        return str(','.join(getattr(self, "addresses", [])))


class MACAddressField(fields.Field):
    """Form field for entering a MAC address with validation.

    Supports all formats known by netaddr.EUI(), for example:
    .. xx:xx:xx:xx:xx:xx
    .. xx-xx-xx-xx-xx-xx
    .. xxxx.xxxx.xxxx
    """
    def validate(self, value):
        super().validate(value)

        if not value:
            return

        try:
            self.mac_address = netaddr.EUI(value)
            # NOTE(rubasov): Normalize MAC address to the most usual format.
            self.mac_address.dialect = netaddr.mac_unix_expanded
        except Exception:
            raise ValidationError(_("Invalid MAC Address format"),
                                  code="invalid_mac")

    def clean(self, value):
        super().clean(value)
        return str(getattr(self, "mac_address", ""))


# NOTE(adriant): The Select widget was considerably rewritten in Django 1.11
# and broke our customizations because we relied on the inner workings of
# this widget as it was written. I've opted to move that older variant of the
# select widget here as a custom widget for Horizon, but this should be
# reviewed and replaced in future. We need to move to template based rendering
# for widgets, but that's a big task better done in Queens.
class SelectWidget(widgets.Widget):
    """
    A custom select widget offering enhanced rendering capabilities.

    Parameters:
        attrs (dict): Initial HTML attributes for the widget.
        choices (iterable): An iterable of 2-tuples to use as choices for the select field.
        data_attrs (iterable of str): Attributes to serialize as data-* attributes on options.
        transform (callable, optional): Function to transform the display value of options.
        transform_html_attrs (callable, optional): Function returning extra HTML attributes for options.
    """

    def __init__(self, attrs=None, choices=(), data_attrs=(), transform=None,
                 transform_html_attrs=None):
        super().__init__(attrs)
        self.choices = list(choices)
        self.data_attrs = data_attrs
        self.transform = transform
        self.transform_html_attrs = transform_html_attrs
    
    def render_option(self, selected, option_value, option_label):
        option_attrs = {
            'value': force_str(option_value),
            'selected': 'selected' if option_value in selected else ''
        }

        if callable(self.transform_html_attrs):
            option_attrs.update(self.transform_html_attrs(option_label))
        
        if self.data_attrs and isinstance(option_label, (list, tuple, dict)):
            for data_attr in self.data_attrs:
                option_attrs[f'data-{data_attr}'] = force_str(getattr(option_label, data_attr, ""))

        if callable(self.transform):
            option_label = self.transform(option_label)
            
        option_attrs_str = flatatt(option_attrs)
        return format_html('<option{}>{}</option>', option_attrs_str, escape(option_label))

    def render_options(self, selected_choices):
        selected_choices = set(force_str(v) for v in selected_choices)
        options = (self.render_option(selected_choices, *choice) for choice in self.choices)
        return format_html_join('\n', '{}', ((option,) for option in options))

    def render(self, name, value, attrs=None, renderer=None):
        value = value or ''
        final_attrs = self.build_attrs(self.attrs, attrs, name=name)
        output = [
            format_html('<select{}>', flatatt(final_attrs)),
            self.render_options([value]),
            '</select>'
        ]
        return mark_safe(''.join(output))

    def build_attrs(self, base_attrs, extra_attrs=None, **kwargs):
        attrs = dict(base_attrs, **kwargs)
        if extra_attrs:
            attrs.update(extra_attrs)
        return attrs

class ThemableSelectWidget(SelectWidget):
    """Bootstrap base select field widget."""
    def render(self, name, value, attrs=None, renderer=None, choices=()):
        # NOTE(woodnt): Currently the "attrs" contents are being added to the
        #               select that's hidden.  It's unclear whether this is the
        #               desired behavior.  In some cases, the attribute should
        #               remain solely on the now-hidden select.  But in others
        #               if it should live on the bootstrap button (visible)
        #               or both.

        new_choices = []
        initial_value = value
        # Initially assuming value is not present in choices.
        value_in_choices = False
        for opt_value, opt_label in itertools.chain(self.choices, choices):
            other_html = self.transform_option_html_attrs(opt_label)

            data_attr_html = self.get_data_attrs(opt_label)
            if data_attr_html:
                other_html += ' ' + data_attr_html

            opt_label = self.transform_option_label(opt_label)

            # If value exists, save off its label for use
            # and setting value in choices to True
            if opt_value == value:
                initial_value = opt_label
                value_in_choices = True

            if other_html:
                new_choices.append((opt_value, opt_label, other_html))
            else:
                new_choices.append((opt_value, opt_label))

        # if value is None or it is not present in choices then set
        # the first value of choices.
        if (value is None or not value_in_choices) and new_choices:
            initial_value = new_choices[0][1]

        attrs = self.build_attrs(attrs)
        id = attrs.pop('id', 'id_%s' % name)

        template = get_template('horizon/common/fields/_themable_select.html')
        context = {
            'name': name,
            'options': new_choices,
            'id': id,
            'value': value,
            'initial_value': initial_value,
            'select_attrs': attrs,
        }
        return template.render(context)


class DynamicSelectWidget(SelectWidget):
    """``Select`` widget to handle dynamic changes to the available choices.

    A subclass of the ``Select`` widget which renders extra attributes for
    use in callbacks to handle dynamic changes to the available choices.
    """
    _data_add_url_attr = "data-add-item-url"

    def render(self, *args, **kwargs):
        add_item_url = self.get_add_item_url()
        if add_item_url is not None:
            self.attrs[self._data_add_url_attr] = add_item_url
        return super().render(*args, **kwargs)

    def get_add_item_url(self):
        if callable(self.add_item_link):
            return self.add_item_link()
        try:
            if self.add_item_link_args:
                return urls.reverse(self.add_item_link,
                                    args=self.add_item_link_args)
            return urls.reverse(self.add_item_link)
        except urls.NoReverseMatch:
            return self.add_item_link


class ThemableDynamicSelectWidget(ThemableSelectWidget, DynamicSelectWidget):
    pass


class ThemableChoiceField(fields.ChoiceField):
    """Bootstrap based select field."""
    widget = ThemableSelectWidget


class DynamicChoiceField(fields.ChoiceField):
    """ChoiceField that make dynamically updating its elements easier.

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
        super().__init__(*args, **kwargs)
        self.widget.add_item_link = add_item_link
        self.widget.add_item_link_args = add_item_link_args


class ThemableDynamicChoiceField(DynamicChoiceField):
    widget = ThemableDynamicSelectWidget


class DynamicTypedChoiceField(DynamicChoiceField, fields.TypedChoiceField):
    """Simple mix of ``DynamicChoiceField`` and ``TypedChoiceField``."""


class ThemableDynamicTypedChoiceField(ThemableDynamicChoiceField,
                                      fields.TypedChoiceField):
    """Simple mix of ``ThemableDynamicChoiceField`` & ``TypedChoiceField``."""


class ThemableCheckboxInput(widgets.CheckboxInput):
    """Checkbox widget which renders extra markup.

    It is used to allow a custom checkbox experience.
    """
    def render(self, name, value, attrs=None, renderer=None):
        label_for = attrs.get('id', '')

        if not label_for:
            attrs['id'] = uuidutils.generate_uuid()
            label_for = attrs['id']

        return html.format_html(
            '<div class="themable-checkbox">{}<label for="{}"></label></div>',
            super().render(name, value, attrs),
            label_for
        )


# NOTE(adriant): SubWidget was removed in Django 1.11 and thus has been moved
# to our codebase until we redo how we handle widgets.
@html.html_safe
class SubWidget(object):
    """SubWidget class from django 1.10.7 codebase

    Some widgets are made of multiple HTML elements -- namely, RadioSelect.
    This is a class that represents the "inner" HTML element of a widget.
    """
    def __init__(self, parent_widget, name, value, attrs, choices):
        self.parent_widget = parent_widget
        self.name, self.value = name, value
        self.attrs, self.choices = attrs, choices

    def __str__(self):
        args = [self.name, self.value, self.attrs]
        if self.choices:
            args.append(self.choices)
        return self.parent_widget.render(*args)


# NOTE(adriant): ChoiceInput and CheckboxChoiceInput were removed in
# Django 1.11 so ChoiceInput has been moved to our codebase until we redo how
# we handle widgets.
@html.html_safe
class ChoiceInput(SubWidget):
    """ChoiceInput class from django 1.10.7 codebase

    An object used by ChoiceFieldRenderer that represents a single
    <input type='$input_type'>.
    """
    input_type = None  # Subclasses must define this

    def __init__(self, name, value, attrs, choice, index):
        self.name = name
        self.value = value
        self.attrs = attrs
        self.choice_value = force_str(choice[0])
        self.choice_label = force_str(choice[1])
        self.index = index
        if 'id' in self.attrs:
            self.attrs['id'] += "_%d" % self.index

    def __str__(self):
        return self.render()

    def render(self, name=None, value=None, attrs=None, renderer=None):
        if self.id_for_label:
            label_for = html.format_html(' for="{}"', self.id_for_label)
        else:
            label_for = ''
        # NOTE(adriant): OrderedDict used to make html attrs order
        # consistent for testing.
        attrs = dict(self.attrs, **attrs) if attrs else self.attrs
        return html.format_html(
            '<label{}>{} {}</label>',
            label_for,
            self.tag(attrs),
            self.choice_label
        )

    def is_checked(self):
        return self.value == self.choice_value

    def tag(self, attrs=None):
        attrs = attrs or self.attrs
        # NOTE(adriant): OrderedDict used to make html attrs order
        # consistent for testing.
        final_attrs = dict(
            attrs,
            type=self.input_type,
            name=self.name,
            value=self.choice_value)
        if self.is_checked():
            final_attrs['checked'] = 'checked'
        return html.format_html('<input{} />', flatatt(final_attrs))

    @property
    def id_for_label(self):
        return self.attrs.get('id', '')


# NOTE(adriant): CheckboxChoiceInput was removed in Django 1.11 so this widget
# has been expanded to include the functionality inherieted previously as a
# temporary solution until we redo how we handle widgets.
class ThemableCheckboxChoiceInput(ChoiceInput):

    input_type = 'checkbox'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # NOTE(e0ne): Django sets default value to None
        if self.value:
            self.value = set(force_str(v) for v in self.value)

    def is_checked(self):
        if self.value:
            return self.choice_value in self.value
        return False

    def render(self, name=None, value=None, attrs=None, renderer=None,
               choices=()):
        if self.id_for_label:
            label_for = html.format_html(' for="{}"', self.id_for_label)
        else:
            label_for = ''
        attrs = dict(self.attrs, **attrs) if attrs else self.attrs
        return html.format_html(
            '<div class="themable-checkbox">{}<label{}>' +
            '<span>{}</span></label></div>',
            self.tag(attrs), label_for, self.choice_label
        )


class ThemableCheckboxSelectMultiple(widgets.CheckboxSelectMultiple):
    choice_input_class = ThemableCheckboxChoiceInput
    _empty_value = []
    outer_html = '<ul{id_attr}>{content}</ul>'
    inner_html = '<li>{choice_value}{sub_widgets}</li>'

    def render(self, name=None, value=None, attrs=None, renderer=None):
        """Outputs a <ul> for this set of choice fields.

        If an id was given to the field, it is applied to the <ul> (each
        item in the list will get an id of `$id_$i`).
        """
        attrs = {} or attrs
        self.attrs = attrs
        self.name = name
        self.value = value

        id_ = self.attrs.get('id')
        output = []
        for i, choice in enumerate(self.choices):
            choice_value, choice_label = choice
            if isinstance(choice_label, (tuple, list)):
                attrs_plus = self.attrs.copy()
                if id_:
                    attrs_plus['id'] += '_{}'.format(i)
                sub_ul_renderer = self.__class__(
                    attrs=attrs_plus,
                    choices=choice_label,
                )
                sub_ul_renderer.choice_input_class = self.choice_input_class
                output.append(html.format_html(
                    self.inner_html, choice_value=choice_value,
                    sub_widgets=sub_ul_renderer.render(),
                ))
            else:
                w = self.choice_input_class(
                    self.name, self.value, self.attrs.copy(), choice, i)
                output.append(html.format_html(
                    self.inner_html,
                    choice_value=force_str(w),
                    sub_widgets=''))
        return html.format_html(
            self.outer_html,
            id_attr=html.format_html(' id="{}"', id_) if id_ else '',
            content=mark_safe('\n'.join(output)),
        )


class ExternalFileField(fields.FileField):
    """Special FileField to upload file to some external location.

    This is a special flavor of FileField which is meant to be used in cases
    when instead of uploading file to Django it should be uploaded to some
    external location, while the form validation is done as usual. It should be
    paired with ExternalUploadMeta metaclass embedded into the Form class.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget.attrs.update({'data-external-upload': 'true'})


class ExternalUploadMeta(forms.DeclarativeFieldsMetaclass):
    """Metaclass to process ExternalFileField fields in a specific way.

    Set this class as the metaclass of a form that contains ExternalFileField
    in order to process ExternalFileField fields in a specific way.
    A hidden CharField twin of FieldField is created which
    contains just the filename (if any file was selected on browser side) and
    a special `clean` method for FileField is defined which extracts just file
    name. This allows to avoid actual file upload to Django server, yet
    process form clean() phase as usual. Actual file upload happens entirely
    on client-side.
    """

    @classmethod
    def __prepare__(cls, name, bases):
        # Required in python 3 to keep the form fields order.
        # Without this method, the __new__(cls, name, bases, attrs) method
        # receives a dict as attrs instead of OrderedDict.
        # This method will be ignored by Python 2.
        return collections.OrderedDict()

    def __new__(cls, name, bases, attrs):
        def get_double_name(name):
            suffix = '__hidden'
            slen = len(suffix)
            return name[:-slen] if name.endswith(suffix) else name + suffix

        def make_clean_method(field_name):
            def _clean_method(self):
                value = self.cleaned_data[field_name]
                if value:
                    self.cleaned_data[get_double_name(field_name)] = value
                return value
            return _clean_method

        # An OrderedDict is required in python 3 to keep the form fields order.
        new_attrs = collections.OrderedDict()
        for attr_name, attr in attrs.items():
            new_attrs[attr_name] = attr
            if isinstance(attr, ExternalFileField):
                hidden_field = fields.CharField(widget=fields.HiddenInput,
                                                required=False)
                new_attr_name = get_double_name(attr_name)
                new_attrs[new_attr_name] = hidden_field
                meth_name = 'clean_' + new_attr_name
                new_attrs[meth_name] = make_clean_method(new_attr_name)
        return super().__new__(cls, name, bases, new_attrs)
