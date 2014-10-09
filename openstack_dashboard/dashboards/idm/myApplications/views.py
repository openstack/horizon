from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import messages
from horizon import tables
from horizon import tabs
from horizon import forms

from openstack_dashboard.dashboards.idm.myApplications \
		 	import tables as application_tables
from openstack_dashboard.dashboards.idm.myApplications \
			import tabs as application_tabs
from openstack_dashboard.dashboards.idm.myApplications \
			import forms as application_forms



class IndexView(tabs.TabbedTableView):
	tab_group_class = application_tabs.PanelTabs
	template_name = 'idm/myApplications/index.html'

  
class CreateView(forms.ModalFormView):
	form_class = application_forms.CreateApplicationForm
	template_name = 'idm/myApplications/create.html'


class UploadImageView(forms.ModalFormView):
	form_class = application_forms.UploadImageForm
	template_name = 'idm/myApplications/upload.html'

class RolesView(forms.ModalFormView):
	form_class = application_forms.RolesApplicationForm
	template_name = 'idm/myApplications/roles.html'

