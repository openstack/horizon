from horizon import tabs as hz_tabs
from . import tabs


class IndexView(hz_tabs.TabbedTableView):  # TabGroupView is fine too; TabbedTableView includes table styles
    tab_group_class = tabs.MonitoringTabs
    template_name = "admin/monitoring/index.html"
