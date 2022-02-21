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
  * @ngdoc overview
  * @ngname horizon.app.core.network_qos.actions.delete-rule.service
  *
  * @description
  * Provides all of the actions for deleting rule to a network qos policy.
  */

  angular
    .module('horizon.app.core.network_qos')
    .factory('horizon.app.core.network_qos.actions.delete-rule.service', deleteRuleService);

  deleteRuleService.$inject = [
    'horizon.app.core.openstack-service-api.neutron',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.app.core.network_qos.actions.deleteRuleWorkflow',
    'horizon.app.core.network_qos.resourceType',
    'horizon.framework.widgets.form.ModalFormService',
    'horizon.framework.widgets.toast.service',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.widgets.modal.deleteModalService'
  ];

  function deleteRuleService(
    neutronAPI,
    policy,
    workflow,
    resourceType,
    modalFormService,
    toast,
    actionResultService
  ) {

    var service = {
      allowed: allowed,
      perform: perform,
      submit: submit
    };

    return service;

    //////////////

    function allowed() {
      return policy.ifAllowed(
        {rules: [['network', 'delete_policy_bandwidth_limit_rule'],
        ['network', 'delete_policy_dscp_marking_rule'],
        ['network', 'delete_policy_minimum_bandwidth_rule']]});
    }

    function perform(qospolicy) {
      if (qospolicy.rules.length !== 0) {
        var config = workflow.init(qospolicy);
        config.title = gettext("Delete Rule");
        config.model.qospolicy = qospolicy.id;
        config.model.qospolicyname = qospolicy.name;
        config.model.rules = qospolicy.rules;
        config.submitText = 'Delete';
        config.submitIcon = 'delete';
        return modalFormService.open(config).then(submit);
      }
      else {
        toast.add('info', interpolate(
            gettext('There are no rules to delete.')));
        return actionResultService.getActionResult().result;
      }
    }

    function submit(context) {
      var id = context.model.qospolicy;
      var ruleid = [context.model.ruleid];
      var ruleType = '';
      angular.forEach(context.model.rules, function(k) {
        if ((k.id).toString() === (ruleid).toString()) {
          ruleType = (k.type).toString();
        }
      }, this);
      if (ruleType === 'bandwidth_limit') {
        return neutronAPI.deleteBandwidthLimitRule(id, ruleid).then(onDeleteRule);
      }
      else if (ruleType === 'dscp_marking') {
        return neutronAPI.deleteDSCPMarkingRule(id, ruleid).then(onDeleteRule);
      }
      else if (ruleType === 'minimum_bandwidth') {
        return neutronAPI.deleteMinimumBandwidthRule(id, ruleid).then(onDeleteRule);
      }
      else if (ruleType === 'minimum_packet_rate') {
        return neutronAPI.deleteMinimumPacketRateRule(id, ruleid).then(onDeleteRule);
      }
    }

    function onDeleteRule() {
      toast.add('success', interpolate(
        gettext('Qos Policy  Rule  was successfully deleted.')));

      return actionResultService.getActionResult()
        .result;
    }
  }

})();
