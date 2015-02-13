# Copyright (C) 2014 Universidad Politecnica de Madrid
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import logging

from django.conf import settings
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm import views as idm_views
from openstack_dashboard.dashboards.idm.users import tables as user_tables
from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm.users.forms import  InfoForm, ContactForm

from horizon import views


# class IndexView(views.APIView):
#     # A very simple class-based view...
#     template_name = 'idm/users/index.html'

#     def get_data(self, request, context, *args, **kwargs):
#         return context

class DetailUserView(tables.MultiTableView):
    template_name = 'idm/users/index.html'
    table_classes = (user_tables.OrganizationsTable,
                     user_tables.ApplicationsTable)

    def get_organizations_data(self):
        organizations = []
        #domain_context = self.request.session.get('domain_context', None)
        try:
            organizations, self._more = api.keystone.tenant_list(
                self.request,
                user=self.request.user.id,
                admin=False)
        except Exception:
            self._more = False
            exceptions.handle(self.request,
                              _("Unable to retrieve organization information."))
        return idm_utils.filter_default_organizations(organizations)

    def get_applications_data(self):
        applications = []
        try:
            applications = fiware_api.keystone.application_list(
                self.request)
                #user=self.request.user.id)
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve application list."))
        return applications

    def get_context_data(self, **kwargs):
        context = super(DetailUserView, self).get_context_data(**kwargs)
        user_id = self.kwargs['user_id']
        user = api.keystone.user_get(self.request, user_id, admin=True)
        context['about_me'] = getattr(user,'description', 'hola')
        context['user.id'] = user.id
        context['user_name'] = user.name
        context['image'] = getattr(user, 'img_original', '/static/dashboard/img/logos/original/user.png')
        context['city'] = getattr(user, 'city', '')
        context['email'] = getattr(user, 'email', '')
        context['website'] = getattr(user, 'website', '')
        return context

class BaseUsersMultiFormView(idm_views.BaseMultiFormView):
    template_name = 'idm/users/edit.html'
    forms_classes = [InfoForm, ContactForm]
    
    def get_endpoint(self, form_class):
        """Override to allow runtime endpoint declaration"""
        endpoints = {
            InfoForm: reverse('horizon:idm:users:info', 
                                kwargs=self.kwargs),
            ContactForm: reverse('horizon:idm:users:contact', 
                                kwargs=self.kwargs),
            # AvatarForm: reverse('horizon:idm:organizations:avatar', 
            #                     kwargs=self.kwargs),
            # CancelForm: reverse('horizon:idm:organizations:cancel', 
            #                     kwargs=self.kwargs),
        }
        return endpoints.get(form_class)

    def get_object(self):
        try:
            return api.keystone.user_get(self.request, self.kwargs['user_id'])
        except Exception:
            redirect = reverse("horizon:idm:users:index")
            exceptions.handle(self.request, 
                    _('Unable to update user'), redirect=redirect)

    def get_initial(self, form_class):
        initial = super(BaseUsersMultiFormView, self).get_initial(form_class)  
        # Existing data from organizations
        initial.update({
            "userID": self.object.id,
            "name": self.object.name,
            "description": getattr(self.object, 'description', ' '),    
            "city": getattr(self.object, 'city', ' '),
            "email": getattr(self.object, 'email', ' '),
            "website":getattr(self.object, 'website', ' '),
        })
        return initial

    def get_context_data(self, **kwargs):

        context = super(BaseUsersMultiFormView, self).get_context_data(**kwargs)
        context['image'] = getattr(self.object, 'img_original', 
                            '/static/dashboard/img/logos/original/user.png')
        return context


class InfoFormHandleView(BaseUsersMultiFormView):    
    form_to_handle_class = InfoForm

class ContactFormHandleView(BaseUsersMultiFormView):
    form_to_handle_class = ContactForm
   
# class AvatarFormHandleView(BaseUsersMultiFormView):
#     form_to_handle_class = AvatarForm

# class CancelFormHandleView(BaseUsersMultiFormView):
#     form_to_handle_class = CancelForm

#     def handle_form(self, form):
#         """ Wrapper for form.handle for easier overriding."""
#         return form.handle(self.request, form.cleaned_data, organization=self.object)
