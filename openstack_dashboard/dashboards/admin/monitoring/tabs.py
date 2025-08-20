from django.conf import settings
from django.utils.translation import gettext_lazy as _
from horizon import tabs
from django.conf import settings

def _norm_path(p: str) -> str:
    return p if p.startswith("/") else ("/" + p)

def _grafana_url():
    vip = getattr(settings, "OPENSTACK_HOST", "127.0.0.1")
    path = _norm_path(getattr(settings, "GRAFANA_PATH", "/"))
    return f"http://{vip}:3200{path}"


def _opensearch_url():
    vip = getattr(settings, "OPENSTACK_HOST", "127.0.0.1")
    path = _norm_path(getattr(settings, "OPENSEARCH_PATH", "/"))
    return f"http://{vip}:5601{path}"

class GrafanaTab(tabs.Tab):
    name = _("Grafana")
    slug = "grafana"
    template_name = "admin/monitoring/_grafana_tab.html"

    def get_context_data(self, request):
        return {"target_url": _grafana_url()}

class OpenSearchTab(tabs.Tab):
    name = _("OpenSearch")
    slug = "opensearch"
    template_name = "admin/monitoring/_opensearch_tab.html"

    def get_context_data(self, request):
        return {"target_url": _opensearch_url()}

class MonitoringTabs(tabs.TabGroup):
    slug = "monitoring_tabs"
    tabs = (GrafanaTab, OpenSearchTab)
    sticky = True
