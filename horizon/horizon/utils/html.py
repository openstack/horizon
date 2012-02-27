import copy

from django.forms.util import flatatt


class HTMLElement(object):
    """ A generic base class that gracefully handles html-style attributes. """
    def __init__(self):
        self.attrs = getattr(self, "attrs", {})
        self.classes = getattr(self, "classes", [])

    def get_default_classes(self):
        """
        Returns a list of default classes which should be combined with any
        other declared classes.
        """
        return []

    @property
    def attr_string(self):
        """
        Returns a flattened string of HTML attributes based on the
        ``attrs`` dict provided to the class.
        """
        final_attrs = copy.copy(self.attrs)
        # Handle css class concatenation
        default = " ".join(self.get_default_classes())
        defined = self.attrs.get('class', '')
        additional = " ".join(getattr(self, "classes", []))
        final_classes = " ".join((defined, default, additional)).strip()
        final_attrs.update({'class': final_classes})
        return flatatt(final_attrs)
