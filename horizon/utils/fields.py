from django.core.exceptions import ValidationError  # noqa
from django.forms import forms
from django.forms import widgets
from django.utils.encoding import force_unicode  # noqa
from django.utils.functional import Promise  # noqa
from django.utils.html import conditional_escape  # noqa
from django.utils.html import escape  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa
import netaddr
import re

ip_allowed_symbols_re = re.compile(r'^[a-fA-F0-9:/\.]+$')
IPv4 = 1
IPv6 = 2


class IPField(forms.Field):
    """
    Form field for entering IP/range values, with validation.
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


class SelectWidget(widgets.Select):
    """
    Customizable select widget, that allows to render
    data-xxx attributes from choices.

    .. attribute:: data_attrs

        Specifies object properties to serialize as
        data-xxx attribute. If passed ('id', ),
        this will be rendered as:
        <option data-id="123">option_value</option>
        where 123 is the value of choice_value.id

    .. attribute:: transform

        A callable used to render the display value
        from the option object.
    """
    def __init__(self, attrs=None, choices=(), data_attrs=(), transform=None):
        self.data_attrs = data_attrs
        self.transform = transform
        super(SelectWidget, self).__init__(attrs, choices)

    def render_option(self, selected_choices, option_value, option_label):
        option_value = force_unicode(option_value)
        other_html = (option_value in selected_choices) and \
                         u' selected="selected"' or ''
        if not isinstance(option_label, (basestring, Promise)):
            for data_attr in self.data_attrs:
                data_value = conditional_escape(
                    force_unicode(getattr(option_label,
                                          data_attr, "")))
                other_html += ' data-%s="%s"' % (data_attr, data_value)

            if self.transform:
                option_label = self.transform(option_label)
        return u'<option value="%s"%s>%s</option>' % (
            escape(option_value), other_html,
            conditional_escape(force_unicode(option_label)))
