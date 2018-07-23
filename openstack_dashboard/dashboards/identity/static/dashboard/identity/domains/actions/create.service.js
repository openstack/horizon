/**
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

(function() {
  'use strict';

  /**
   * @ngdoc factory
   * @name horizon.dashboard.identity.domains.actions.create.service
   * @description
   * Service for the domain create modal
   */
  angular
    .module('horizon.dashboard.identity.domains.actions')
    .factory('horizon.dashboard.identity.domains.actions.create.service', createService);

  createService.$inject = [
    '$q',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.dashboard.identity.domains.actions.workflow.service',
    'horizon.dashboard.identity.domains.resourceType',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.widgets.form.ModalFormService',
    'horizon.framework.widgets.toast.service'
  ];

  function createService(
    $q, keystone, policy, workflow, resourceType, actionResult, modal, toast
  ) {

    var service = {
      allowed: allowed,
      perform: perform
    };

    return service;

    ///////

    function allowed() {
      return $q.all([
        keystone.canEditIdentity('domain'),
        policy.ifAllowed({ rules: [['identity', 'create_domain']] })
      ]);
    }

    function perform() {
      var config = workflow.init();
      config.title = gettext("Create Domain");
      return modal.open(config).then(submit);
    }

    function submit(context) {
      return keystone.createDomain(context.model).then(success);
    }

    function success(response) {
      var domain = response.data;
      var message = gettext('Domain %s was successfully created.');
      toast.add('success', interpolate(message, [domain.name]));
      return actionResult.getActionResult().created(resourceType, domain.id).result;
    }
  }
})();
