# -*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy as _

TABS = [
    {"slug": "overview",  "name": _("Overview")},
    {"slug": "services",  "name": _("OpenStack Services")},
    {"slug": "rabbitmq",  "name": _("RabbitMQ")},
    {"slug": "mariadb",   "name": _("MariaDB")},
    {"slug": "containers","name": _("Containers")},
    {"slug": "raw",       "name": _("Raw JSON")},
]
