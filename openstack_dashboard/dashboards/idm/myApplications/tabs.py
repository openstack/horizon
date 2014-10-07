from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.api import keystone
from openstack_dashboard import policy
# from openstack_dashboard.dashboards.idm.myApplications import tables

from openstack_dashboard.dashboards.idm.myApplications \
    import tables as applications_table


class ProvidingTab(tabs.TableTab):
    name = _("Providing")
    slug = "providing_tab"
    table_classes = (applications_table.ProvidingApplicationsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

   

    def get_providing_table_data(self):
        applications = []
        return applications

class PurchasedTab(tabs.TableTab):
    name = _("Purchased")
    slug = "purchased_tab"
    table_classes = (applications_table.PurchasedApplicationsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

   

    def get_purchased_table_data(self):
        applications = []
        return applications

        

class PanelTabs(tabs.TabGroup):
    slug = "panel_tabs"
    tabs = (ProvidingTab, PurchasedTab)
    sticky = True