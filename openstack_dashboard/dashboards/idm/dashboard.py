from django.utils.translation import ugettext_lazy as _

import horizon


class Idm(horizon.Dashboard):
    name = _("Identity Manager")
    slug = "idm"
    panels = ('home', 'home_orgs', 'organizations', 'members', 'myApplications', 'users' )  # Add your panels here.
    default_panel = 'home'  # Specify the slug of the dashboard's default panel.


    def nav(self,context):
        if context['request'].organization.id != context['request'].user.default_project_id:
            default_panel = 'home_orgs'
            return True
        else:
            default_panel = 'home'
            return True




horizon.register(Idm)
