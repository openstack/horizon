/*
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

(function() {
  'use strict';

  /**
   * @ngdoc factory
   * @name horizon.app.core.server_groups.actions.workflow.service
   * @ngController
   *
   * @description
   * Workflow for creating server group
   */
  angular
    .module('horizon.app.core.server_groups.actions')
    .factory('horizon.app.core.server_groups.actions.workflow.service', ServerGroupWorkflow);

  ServerGroupWorkflow.$inject = [
    'horizon.app.core.server_groups.service'
  ];

  function ServerGroupWorkflow(serverGroupsService) {

    var workflow = {
      init: init
    };

    function init() {
      var schema = {
        type: 'object',
        properties: {
          name: {
            title: gettext('Name'),
            type: 'string'
          },
          policy: {
            title: gettext('Policy'),
            type: 'string'
          }
        },
        required: ['name', 'policy']
      };

      var form = [
        "name",
        {
          key: "policy",
          type: "select",
          titleMap: []
        }
      ];

      var model = {};

      var config = {
        schema: schema,
        form: form,
        model: model
      };

      serverGroupsService.getServerGroupPolicies().then(modifyPolicies);
      function modifyPolicies(policies) {
        var policyField = config.form[1];
        angular.forEach(policies, function(k, v) {
          this.push({name: k, value: v});
        }, policyField.titleMap);
      }

      return config;
    }

    return workflow;
  }
})();
