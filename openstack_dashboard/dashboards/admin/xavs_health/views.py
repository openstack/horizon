# -*- coding: utf-8 -*-
import json
from django.utils.translation import gettext_lazy as _
from horizon import views

from openstack_dashboard.dashboards.admin.xavs_health.collect import gather


def _as_list(value):
    if isinstance(value, list):
        return value
    return list(value or [])


class IndexView(views.HorizonTemplateView):
    template_name = "admin/xavs_health/index.html"
    page_title = _("XAVS Health")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        data = {}
        errors = []
        try:
            data = gather() or {}
        except Exception as e:
            errors.append(str(e))

        services = _as_list(data.get("openstack_services"))
        containers = _as_list(data.get("containers"))
        rabbitmq = data.get("rabbitmq") or {}
        mariadb = data.get("mariadb") or {}

        svc_up = sum(1 for r in services if str(r.get("status", "")).lower() == "up")
        svc_down = sum(1 for r in services if str(r.get("status", "")).lower() == "down")
        svc_warn = sum(1 for r in services if str(r.get("status", "")).lower() == "warn")

        ctx.update({
            "health": data,
            "health_json": json.dumps(data, separators=(",", ":"), ensure_ascii=False),
            "services": services,
            "containers": containers,
            "rabbitmq": rabbitmq,
            "mariadb": mariadb,
            "errors": _as_list(data.get("errors")) + errors,
            "summary": {
                "services_total": len(services),
                "services_up": svc_up,
                "services_warn": svc_warn,
                "services_down": svc_down,
                "rabbitmq_up": bool(rabbitmq.get("cluster_up")),
                "mariadb_ready": bool(mariadb.get("ready")),
                "mariadb_size": mariadb.get("cluster_size"),
            },
        })
        return ctx
