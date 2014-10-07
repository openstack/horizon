
from horizon import forms
from openstack_dashboard import api
from openstack_dashboard.dashboards.settings.useremail import forms as useremail_forms


class EmailView(forms.ModalFormView):
    form_class = useremail_forms.EmailForm
    template_name = 'settings/useremail/change.html'

    def get_form_kwargs(self):
        kwargs = super(EmailView, self).get_form_kwargs()
        user_id=self.request.user.id
        user = api.keystone.user_get(self.request,user_id,admin=False)
        kwargs['initial']['email'] = user.email
        return kwargs

