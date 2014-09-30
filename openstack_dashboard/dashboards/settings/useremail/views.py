from horizon import forms
from openstack_dashboard.dashboards.settings.useremail import forms as useremail_forms

class EmailView(forms.ModalFormView):
    form_class = useremail_forms.EmailForm
    template_name = 'settings/useremail/change.html'

