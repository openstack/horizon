# Copyright 2013 CentRin Data, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json
from typing import Any, Iterable, List, Optional

from django.utils.translation import gettext_lazy as _
from django.views.decorators.debug import sensitive_variables
from django.utils.encoding import force_str

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.instances import utils as instance_utils


# -----------------------------
# Helpers (tuple/dict safe)
# -----------------------------

def _flavor_id(obj: Any) -> Optional[str]:
    """Return flavor id from a nova Flavor object, (id, name) tuple, or dict."""
    if obj is None:
        return None
    # nova flavor object
    if hasattr(obj, "id"):
        return getattr(obj, "id")
    # (id, name) tuple/list
    if isinstance(obj, (tuple, list)) and obj:
        return obj[0]
    # {"id": ..., ...}
    if isinstance(obj, dict):
        return obj.get("id")
    return None


def _ensure_flavor_obj(request, obj: Any):
    """Return a nova Flavor object, fetching by id if necessary. Returns None on failure."""
    if hasattr(obj, "_info") and hasattr(obj, "id"):
        return obj
    fid = _flavor_id(obj)
    if not fid:
        return None
    try:
        return api.nova.flavor_get(request, fid)
    except Exception:
        return None


class SetFlavorChoiceAction(workflows.Action):
    old_flavor_id = forms.CharField(required=False, widget=forms.HiddenInput())
    old_flavor_name = forms.CharField(
        label=_("Old Flavor"),
        widget=forms.TextInput(attrs={"readonly": "readonly"}),
        required=False,
    )
    flavor = forms.ThemableChoiceField(
        label=_("New Flavor"),
        help_text=_("Choose the flavor to launch."),
    )

    class Meta(object):
        name = _("Flavor Choice")
        slug = "flavor_choice"
        help_text_template = "project/instances/_flavors_and_quotas.html"

    def populate_flavor_choices(self, request, context):
        """Provide (id, name) choices for the select.
        Use Horizon's helper to list flavors, but convert robustly.
        """
        choices = []
        try:
            flavors = instance_utils.flavor_list(request)
            if flavors:
                # Try to sort via helper if it expects objects; otherwise ignore
                try:
                    flavors = instance_utils.sort_flavor_list(request, flavors)
                except Exception:
                    pass
                for f in flavors:
                    fid = _flavor_id(f)
                    name = getattr(f, "name", None)
                    if name is None and isinstance(f, (tuple, list)) and len(f) > 1:
                        name = f[1]
                    if name is None and isinstance(f, dict):
                        name = f.get("name")
                    if fid and name:
                        choices.append((fid, name))
        except Exception:
            exceptions.handle(request, _("Unable to retrieve instance flavors."))
        return choices

    def get_help_text(self, extra_context=None):
        extra = {} if extra_context is None else dict(extra_context)
        try:
            # Quota data for the progress bars in the help template
            extra["usages"] = api.nova.tenant_absolute_limits(self.request, reserved=True)
            extra["usages_json"] = json.dumps(extra["usages"])  # for JS

            # === XLOUD PATCH: embed flavor extra_specs server-side ===
            # Build a JSON array of flavor _info dicts with extra_specs injected.
            enriched: List[dict] = []
            base_list: Iterable[Any]
            try:
                base_list = instance_utils.flavor_list(self.request)
            except Exception:
                base_list = []

            for item in base_list:
                fl = _ensure_flavor_obj(self.request, item)
                if not fl:
                    continue
                # Fetch extras raw mapping {key: value}
                try:
                    extras = api.nova.flavor_get_extras(self.request, fl.id, raw=True)
                except Exception:
                    extras = {}
                # Copy info and inject extras
                info = dict(getattr(fl, "_info", {}))
                # expose RAM as MB and GB for client-side display
                try:
                    ram_mb = int(getattr(fl, 'ram', info.get('ram', 0)) or 0)
                except Exception:
                    try:
                        ram_mb = int(info.get('ram', 0) or 0)
                    except Exception:
                        ram_mb = 0
                info['ram_mb'] = ram_mb
                info['ram_gb'] = round(float(ram_mb) / 1024.0, 2)
                info["OS-FLV-WITH-EXT-SPECS:extra_specs"] = extras
                enriched.append(info)

            extra["flavors"] = json.dumps(enriched)
            extra["resize_instance"] = True
        except Exception:
            exceptions.handle(self.request, _("Unable to retrieve quota information."))
        return super().get_help_text(extra)


class SetFlavorChoice(workflows.Step):
    action_class = SetFlavorChoiceAction
    depends_on = ("instance_id", "name")
    contributes = ("old_flavor_id", "old_flavor_name", "flavors", "flavor")


class ResizeInstance(workflows.Workflow):
    slug = "resize_instance"
    name = _("Resize Instance")
    finalize_button_name = _("Resize")
    success_message = _("Resizing %(name)s.")
    failure_message = _("%(name)s unable to be resized.")
    success_url = "horizon:project:instances:index"
    default_steps = (SetFlavorChoice,)

    def format_status_message(self, message):
        name = self.context.get("name", "unknown instance")
        try:
            if "%(action" in message:
                # keep previous behavior for action-based messages
                message = _("%(action)s %(name)s.")
                return message % {"action": _("Resizing"), "name": name}
            if "%(name" in message:
                return message % {"name": name}
            if "%s" in message:
                return message % name
        except Exception:
            pass
        return message

    @sensitive_variables("context")
    def handle(self, request, context):
        instance_id = context.get("instance_id")
        flavor = context.get("flavor")
        try:
            api.nova.server_resize(request, instance_id, flavor)
            return True
        except Exception as e:
            self.failure_message = force_str(e)
            return False
