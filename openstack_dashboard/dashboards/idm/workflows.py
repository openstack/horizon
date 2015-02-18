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

import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard.dashboards.idm import utils as idm_utils



LOG = logging.getLogger('idm_logger')
RELATIONSHIP_SLUG = "update_owners"

class RelationshipApiInterface(object):
    """Holds the api calls for each specific relationship"""
    
    def _list_all_owners(self, request, superset_id):
        pass

    def _list_all_objects(self, request, superset_id):
        pass

    def _list_current_assignments(self, request, superset_id):
        pass

    def _get_default_object(self, request):
        pass

    def _add_object_to_owner(self, request, superset, owner, obj):
        pass

    def _remove_object_from_owner(self, request, superset, owner, obj):
        pass

    def _get_supersetid_name(self, request, superset_id):
        pass


class RelationshipConsumerMixin(object):
    RELATIONSHIP_CLASS = None
    def _load_relationship_api(self):
        return self.RELATIONSHIP_CLASS()

class UpdateRelationshipAction(workflows.MembershipAction, 
                            RelationshipConsumerMixin):
    ERROR_MESSAGE = _('Unable to retrieve data. Please try again later.')
    ERROR_URL = ''

    def __init__(self, request, *args, **kwargs):
        super(UpdateRelationshipAction, self).__init__(request,
                                                         *args,
                                                         **kwargs)
        self.relationship = self._load_relationship_api()
        self.superset_id = self._get_superset_id()

        # Get the default role
        try:
            default_object = self.relationship._get_default_object(request)
        except Exception:
            exceptions.handle(request,
                              self.ERROR_MESSAGE,
                              redirect=reverse(self.ERROR_URL))
        if default_object:
            self._init_default_object_field(default_object)
        
        # Get list of available owners
        try:
            owners_list = self.relationship._list_all_owners(request, 
                                                self.superset_id)
        except Exception:
            exceptions.handle(request,
                              self.ERROR_MESSAGE,
                              redirect=reverse(self.ERROR_URL))
        # Get list of objects
        try:
            object_list = self.relationship._list_all_objects(request, 
                                                self.superset_id)
        except Exception:
            exceptions.handle(request,
                              self.ERROR_MESSAGE,
                              redirect=reverse(self.ERROR_URL))
        self._init_object_fields(object_list, owners_list)
        
        # Figure out owners & objects
        try:
            owners_objects_relationship = \
                self.relationship._list_current_assignments(request, 
                                                self.superset_id)
        except Exception:
            exceptions.handle(request,
                              self.ERROR_MESSAGE,
                              redirect=reverse(self.ERROR_URL))
       
        # Flag the alredy owned ones
        self._init_current_assignments(owners_objects_relationship)


    def _init_default_object_field(self, default_object):
        default_object_name = self.get_default_role_field_name()
        self.fields[default_object_name] = forms.CharField(required=False)
        self.fields[default_object_name].initial = default_object.id

    def _init_object_fields(self, object_list, owners_list):
        relationship = self._load_relationship_api()
        for obj in object_list:
            field_name = self.get_member_field_name(obj.id)
            label = obj.name
            widget = forms.widgets.SelectMultiple(attrs={
                'data-superset-name': 
                    relationship._get_supersetid_name(self.request, 
                                                      self.superset_id),
                'data-superset-id':self.superset_id
            })
            self.fields[field_name] = forms.MultipleChoiceField(
                                                    required=False,
                                                    label=label,
                                                    widget=widget)
            self.fields[field_name].choices = owners_list
            self.fields[field_name].initial = []

    def _init_current_assignments(self, owners_objects_relationship):
        for owner_id in owners_objects_relationship:
            objects_ids = owners_objects_relationship[owner_id]
            for object_id in objects_ids:
                field_name = self.get_member_field_name(object_id)
                self.fields[field_name].initial.append(owner_id)

    def _get_superset_id(self):
        return self.initial['superset_id']

    class Meta:
        slug = RELATIONSHIP_SLUG


class UpdateRelationshipStep(workflows.UpdateMembersStep, 
                            RelationshipConsumerMixin):
    action_class = UpdateRelationshipAction
    contributes = ("superset_id",)

    def contribute(self, data, context):
        superset_id = context['superset_id']
        if data:
            self.relationship = self._load_relationship_api()
            try:
                object_list = self.relationship._list_all_objects(
                    self.workflow.request, superset_id)
            except Exception:
                exceptions.handle(self.workflow.request,
                                  _('Unable to retrieve list.'))

            post = self.workflow.request.POST
            for obj in object_list:
                field = self.get_member_field_name(obj.id)
                context[field] = post.getlist(field)
        return context


class RelationshipWorkflow(workflows.Workflow, 
                            RelationshipConsumerMixin):
    default_steps = (UpdateRelationshipStep,)
    member_slug = RELATIONSHIP_SLUG
    def handle(self, request, data):
        superset_id = data['superset_id']
        member_step = self.get_step(self.member_slug)
        self.relationship = self._load_relationship_api()
        try:
            object_list = self.relationship._list_all_objects(
                request, superset_id)
            owners_objects_relationship = \
                self.relationship._list_current_assignments(request,
                                                            superset_id)
            # re-index by object with a owner list for easier processing 
            # in later steps
            current_objects = idm_utils.swap_dict(owners_objects_relationship)

            # Parse the form data
            modified_objects = {}
            for obj in object_list:
                field_name = member_step.get_member_field_name(obj.id)
                modified_objects[obj.id] = data[field_name]
            
            # Create the delete and add sets
            objects_to_add, objects_to_delete = \
                self._create_add_and_delete_sets(modified_objects, 
                                                 current_objects)
            # Add the objects
            for object_id in objects_to_add:
                for owner_id in objects_to_add[object_id]:
                  self.relationship._add_object_to_owner(
                    self.request,
                    superset=superset_id,
                    owner=owner_id,
                    obj=object_id)
            # Remove the objects
            for object_id in objects_to_delete:
                for owner_id in objects_to_delete[object_id]:
                   self.relationship._remove_object_from_owner(
                        self.request,
                        superset=superset_id,
                        owner=owner_id,
                        obj=object_id)
            return True
        except Exception:
            exceptions.handle(request,
                          _('Failed to modify organization\'s members.'))
            return False

    def _create_add_and_delete_sets(self, modified_objects, current_objects):
        objects_to_add = {}
        objects_to_delete = {}
        for object_id in modified_objects:
            new_owners = set(modified_objects.get(object_id, []))
            current_owners = set(current_objects.get(object_id, []))
            # owners to add-> owners in N and not in C -> N-C
            owners_to_add = new_owners - current_owners
            if owners_to_add:
                objects_to_add[object_id] = owners_to_add
            # owners to delete -> owners in C and not in N -> C-N
            owners_to_delete = current_owners - new_owners
            if owners_to_delete:
                objects_to_delete[object_id] = owners_to_delete
        return objects_to_add, objects_to_delete
