from horizon import forms
from openstack_dashboard.dashboards.settings.cancelaccount import forms as cancel_forms

class CancelView(forms.ModalFormView):
    form_class = cancel_forms.BasicCancelForm
    template_name = 'settings/cancelaccount/cancel.html'
