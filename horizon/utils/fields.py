import re
import netaddr
from django.core.exceptions import ValidationError
from django.forms import forms
from django.utils.translation import ugettext as _

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
        except:
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
