from horizon import tabs as hz_tabs
from . import tabs


class IndexView(hz_tabs.TabbedTableView):  # TabGroupView is fine too; TabbedTableView includes table styles
    tab_group_class = tabs.LoggingTabs
    template_name = "admin/logging/index.html"
