from django.conf import settings
from django.utils.translation import gettext_lazy as _
from horizon import tabs
from django.conf import settings

def _norm_path(p: str) -> str:
    return p if p.startswith("/") else ("/" + p)

def _opensearch_url():
    vip = getattr(settings, "OPENSTACK_HOST", "127.0.0.1")
    path = _norm_path(getattr(settings, "OPENSEARCH_PATH", "/"))
    return f"http://{vip}:5601{path}"


class OpenSearchTab(tabs.Tab):
    name = _("OpenSearch")
    slug = "opensearch"
    template_name = "admin/logging/_opensearch_tab.html"

    def get_context_data(self, request):
        return {"target_url": _opensearch_url()}

class LoggingTabs(tabs.TabGroup):
    slug = "logging_tabs"
    tabs = (OpenSearchTab,OpenSearchTab)
    sticky = True
