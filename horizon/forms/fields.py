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

import itertools
import re

import netaddr
import six

from oslo_utils import uuidutils

from django.core.exceptions import ValidationError
from django.core import urlresolvers
from django.forms import fields
from django.forms import forms
from django.forms.utils import flatatt
from django.forms import widgets
from django.template.loader import get_template
from django.utils.encoding import force_text
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import Promise
from django.utils import html
from django.utils.safestring import mark_safe
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


class MACAddressField(fields.Field):
    """Form field for entering a MAC address with validation.

    Supports all formats known by netaddr.EUI(), for example:
    .. xx:xx:xx:xx:xx:xx
    .. xx-xx-xx-xx-xx-xx
    .. xxxx.xxxx.xxxx
    """
    def validate(self, value):
        super(MACAddressField, self).validate(value)

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
        super(MACAddressField, self).clean(value)
        return str(getattr(self, "mac_address", ""))


# NOTE(adriant): The Select widget was considerably rewritten in Django 1.11
# and broke our customizations because we relied on the inner workings of
# this widget as it was written. I've opted to move that older variant of the
# select widget here as a custom widget for Horizon, but this should be
# reviewed and replaced in future. We need to move to template based rendering
# for widgets, but that's a big task better done in Queens.
class SelectWidget(widgets.Widget):
    """Custom select widget.

    It allows to render data-xxx attributes from choices.
    This widget also allows user to specify additional html attributes
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

            widget=forms.ThemableSelect( attrs={'class': 'switchable',
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
        self.choices = list(choices)
        self.data_attrs = data_attrs
        self.transform = transform
        self.transform_html_attrs = transform_html_attrs
        super(SelectWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        output = [html.format_html('<select{}>', flatatt(final_attrs))]
        options = self.render_options([value])
        if options:
            output.append(options)
        output.append('</select>')
        return mark_safe('\n'.join(output))

    def build_attrs(self, extra_attrs=None, **kwargs):
        "Helper function for building an attribute dictionary."
        attrs = dict(self.attrs, **kwargs)
        if extra_attrs:
            attrs.update(extra_attrs)
        return attrs

    def render_option(self, selected_choices, option_value, option_label):
        option_value = force_text(option_value)
        other_html = (u' selected="selected"'
                      if option_value in selected_choices else '')

        other_html += self.transform_option_html_attrs(option_label)

        data_attr_html = self.get_data_attrs(option_label)
        if data_attr_html:
            other_html += ' ' + data_attr_html

        option_label = self.transform_option_label(option_label)

        return u'<option value="%s"%s>%s</option>' % (
            html.escape(option_value), other_html, option_label)

    def render_options(self, selected_choices):
        # Normalize to strings.
        selected_choices = set(force_text(v) for v in selected_choices)
        output = []
        for option_value, option_label in self.choices:
            if isinstance(option_label, (list, tuple)):
                output.append(html.format_html(
                    '<optgroup label="{}">', force_text(option_value)))
                for option in option_label:
                    output.append(
                        self.render_option(selected_choices, *option))
                output.append('</optgroup>')
            else:
                output.append(self.render_option(
                    selected_choices, option_value, option_label))
        return '\n'.join(output)

    def get_data_attrs(self, option_label):
        other_html = []
        if not isinstance(option_label, (six.string_types, Promise)):
            for data_attr in self.data_attrs:
                data_value = html.conditional_escape(
                    force_text(getattr(option_label,
                                       data_attr, "")))
                other_html.append('data-%s="%s"' % (data_attr, data_value))
        return ' '.join(other_html)

    def transform_option_label(self, option_label):
        if (not isinstance(option_label, (six.string_types, Promise)) and
                callable(self.transform)):
                    option_label = self.transform(option_label)
        return html.conditional_escape(force_text(option_label))

    def transform_option_html_attrs(self, option_label):
        if not callable(self.transform_html_attrs):
            return ''
        return flatatt(self.transform_html_attrs(option_label))


class ThemableSelectWidget(SelectWidget):
    """Bootstrap base select field widget."""
    def render(self, name, value, attrs=None, choices=()):
        # NOTE(woodnt): Currently the "attrs" contents are being added to the
        #               select that's hidden.  It's unclear whether this is the
        #               desired behavior.  In some cases, the attribute should
        #               remain solely on the now-hidden select.  But in others
        #               if it should live on the bootstrap button (visible)
        #               or both.

        new_choices = []
        initial_value = value
        for opt_value, opt_label in itertools.chain(self.choices, choices):
            other_html = self.transform_option_html_attrs(opt_label)

            data_attr_html = self.get_data_attrs(opt_label)
            if data_attr_html:
                other_html += ' ' + data_attr_html

            opt_label = self.transform_option_label(opt_label)

            # If value exists, save off its label for use
            if opt_value == value:
                initial_value = opt_label

            if other_html:
                new_choices.append((opt_value, opt_label, other_html))
            else:
                new_choices.append((opt_value, opt_label))

        if value is None and new_choices:
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
        super(DynamicChoiceField, self).__init__(*args, **kwargs)
        self.widget.add_item_link = add_item_link
        self.widget.add_item_link_args = add_item_link_args


class ThemableDynamicChoiceField(DynamicChoiceField):
    widget = ThemableDynamicSelectWidget


class DynamicTypedChoiceField(DynamicChoiceField, fields.TypedChoiceField):
    """Simple mix of ``DynamicChoiceField`` and ``TypedChoiceField``."""
    pass


class ThemableDynamicTypedChoiceField(ThemableDynamicChoiceField,
                                      fields.TypedChoiceField):
    """Simple mix of ``ThemableDynamicChoiceField`` & ``TypedChoiceField``."""
    pass


class ThemableCheckboxInput(widgets.CheckboxInput):
    """Checkbox widget which renders extra markup.

    It is used to allow a custom checkbox experience.
    """
    def render(self, name, value, attrs=None):
        label_for = attrs.get('id', '')

        if not label_for:
            attrs['id'] = uuidutils.generate_uuid()
            label_for = attrs['id']

        return html.format_html(
            u'<div class="themable-checkbox">{}<label for="{}"></label></div>',
            super(ThemableCheckboxInput, self).render(name, value, attrs),
            label_for
        )


# NOTE(adriant): SubWidget was removed in Django 1.11 and thus has been moved
# to our codebase until we redo how we handle widgets.
@html.html_safe
@python_2_unicode_compatible
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
@python_2_unicode_compatible
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
        self.choice_value = force_text(choice[0])
        self.choice_label = force_text(choice[1])
        self.index = index
        if 'id' in self.attrs:
            self.attrs['id'] += "_%d" % self.index

    def __str__(self):
        return self.render()

    def render(self, name=None, value=None, attrs=None):
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
        super(ThemableCheckboxChoiceInput, self).__init__(*args, **kwargs)
        # NOTE(e0ne): Django sets default value to None
        if self.value:
            self.value = set(force_text(v) for v in self.value)

    def is_checked(self):
        if self.value:
            return self.choice_value in self.value
        return False

    def render(self, name=None, value=None, attrs=None, choices=()):
        if self.id_for_label:
            label_for = html.format_html(' for="{}"', self.id_for_label)
        else:
            label_for = ''
        attrs = dict(self.attrs, **attrs) if attrs else self.attrs
        return html.format_html(
            u'<div class="themable-checkbox">{}<label{}>' +
            u'<span>{}</span></label></div>',
            self.tag(attrs), label_for, self.choice_label
        )


class ThemableCheckboxSelectMultiple(widgets.CheckboxSelectMultiple):
    choice_input_class = ThemableCheckboxChoiceInput
    _empty_value = []
    outer_html = '<ul{id_attr}>{content}</ul>'
    inner_html = '<li>{choice_value}{sub_widgets}</li>'

    def render(self, name=None, value=None, attrs=None):
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
                    name=self.name,
                    value=self.value,
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
                    choice_value=force_text(w),
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
        super(ExternalFileField, self).__init__(*args, **kwargs)
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
    def __new__(mcs, name, bases, attrs):
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

        new_attrs = {}
        for attr_name, attr in attrs.items():
            new_attrs[attr_name] = attr
            if isinstance(attr, ExternalFileField):
                hidden_field = fields.CharField(widget=fields.HiddenInput,
                                                required=False)
                hidden_field.creation_counter = attr.creation_counter + 1000
                new_attr_name = get_double_name(attr_name)
                new_attrs[new_attr_name] = hidden_field
                meth_name = 'clean_' + new_attr_name
                new_attrs[meth_name] = make_clean_method(new_attr_name)
        return super(ExternalUploadMeta, mcs).__new__(
            mcs, name, bases, new_attrs)
