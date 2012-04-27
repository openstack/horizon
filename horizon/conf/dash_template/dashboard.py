from django.utils.translation import ugettext_lazy as _

import horizon


class {{ dash_name|title }}(horizon.Dashboard):
    name = _("{{ dash_name|title }}")
    slug = "{{ dash_name|slugify }}"
    panels = ()  # Add your panels here.
    default_panel = ''  # Specify the slug of the dashboard's default panel.


horizon.register({{ dash_name|title }})
