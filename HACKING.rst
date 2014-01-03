Horizon Style Commandments
==========================

- Step 1: Read the OpenStack Style Commandments
  http://docs.openstack.org/developer/hacking/
- Step 2: The following names can be imported directly, without triggering the
  "H302: import only modules" flake8 warning::

    collections.defaultdict,
    django.conf.settings,
    django.core.urlresolvers.reverse,
    django.core.urlresolvers.reverse_lazy,
    django.template.loader.render_to_string,
    django.utils.datastructures.SortedDict,
    django.utils.encoding.force_unicode,
    django.utils.html.conditional_escape,
    django.utils.html.escape,
    django.utils.http.urlencode,
    django.utils.safestring.mark_safe,
    django.utils.translation.pgettext_lazy,
    django.utils.translation.ugettext_lazy,
    django.utils.translation.ungettext_lazy,
    operator.attrgetter,
    StringIO.StringIO

- Step 3: Read on

Horizon Specific Commandments
-----------------------------

- Read the Horizon contributing documentation at http://docs.openstack.org/developer/horizon/contributing.html
