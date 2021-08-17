/* Liscensed under the Apache License, Version 2.0 (the "License");
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
   * @name horizon.app.core.network_qos.actions.delete-rule.workflow.service
   * @ngController
   *
   * @description
   * Workflow for deleting rule to a network qos policy.
   */

  angular
    .module('horizon.app.core.network_qos.actions')
    .factory('horizon.app.core.network_qos.actions.deleteRuleWorkflow', deleteRuleWorkflow);

  deleteRuleWorkflow.$inject = [
    'horizon.app.core.openstack-service-api.neutron'
  ];

  function deleteRuleWorkflow(neutronAPI) {

    var workflow = {
      init: init
    };

    function init(qospolicy) {
      var schema = {
        type: 'object',
        properties: {
          qospolicyname: {
            title: gettext('QoS Policy Name'),
            type: 'string',
            readOnly: true
          },
          ruleid: {
            title: gettext('Rule'),
            type: 'string'
          },
          qospolicy: {
            title: gettext('QoS Policy ID'),
            type: 'string',
            readOnly: true
          }
        },
        required: ['ruleid']
      };

      var form = [
        "qospolicy",
        "qospolicyname",
        {
          key: "ruleid",
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

      neutronAPI.getQosPolicy(qospolicy.id).then(modifyPolicies);

      function modifyPolicies(policies) {
        var policyField = config.form[2];
        angular.forEach(policies.data.rules, function(k) {
          if (k.type === 'dscp_marking') {
            this.push({
              name: String(k.id + ' - ' + k.type + ' - dscpmark: ' + k.dscp_mark),
              value: String(k.id)
            });
          }
          else if (k.type === 'bandwidth_limit') {
            this.push({
              name: String(k.id + ' - ' + k.type + ' - maxkbps: ' + k.max_kbps +
                  ', maxburstkbps: ' + k.max_burst_kbps + ', ' + k.direction),
              value: String(k.id)
            });
          }
          else if (k.type === 'minimum_bandwidth') {
            this.push({
              name: String(k.id + ' - ' + k.type + ' - minkbps: ' +
                  k.min_kbps + ', ' + k.direction),
              value: String(k.id)
            });
          }
          else if (k.type === 'minimum_packet_rate') {
            this.push({
              name: String(k.id + ' - ' + k.type + ' - minkpps: ' +
                  k.min_kpps + ', ' + k.direction),
              value: String(k.id)
            });
          }
        }, policyField.titleMap);
      }
      return config;
    }
    return workflow;
  }
})();
