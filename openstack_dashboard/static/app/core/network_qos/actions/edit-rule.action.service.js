/* Licensed under the Apache License, Version 2.0 (the "License");
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
  * @ngname horizon.app.core.network_qos.actions.edit-rule.service
  *
  * @description
  * Provides all of the actions for editing rule to a network qos policy.
  */

  angular
    .module('horizon.app.core.network_qos')
    .factory('horizon.app.core.network_qos.actions.edit-rule.service', editRuleService);

  editRuleService.$inject = [
    'horizon.app.core.openstack-service-api.neutron',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.app.core.network_qos.resourceType',
    'horizon.framework.widgets.form.ModalFormService',
    'horizon.framework.widgets.toast.service',
    'horizon.framework.util.actions.action-result.service',
    'horizon.app.core.network_qos.basePath'
  ];

  function editRuleService(
    neutronAPI,
    policy,
    resourceType,
    modalFormService,
    toast,
    actionResultService,
    basePath
  ) {

    var caption = gettext("Edit Rule");

    var schema = {
      type: 'object',
      properties: {
        qospolicy: {
          title: gettext('QoSPolicyId'),
          type: 'string',
          readOnly: true
        },
        qospolicyname: {
          title: gettext('QoSPolicyName'),
          type: 'string',
          readOnly: true
        },
        ruleid: {
          title: gettext('RuleId'),
          type: 'string'
        }
      },
      required: ['ruleid']
    };

    var form = [
      {
        type: "section",
        htmlClass: "row",
        items: [
          {
            type: "section",
            htmlClass: "col-sm-12",
            items: [
              {
                key: ["qospolicy", "qospolicyname", "type"],
                type: "template",
                templateUrl: basePath + "actions/edit-rule.html"
              }
            ]
          }
        ]
      }
    ];

    var model = {};

    var service = {
      allowed: allowed,
      perform: perform,
      submit: submit
    };

    return service;

    //////////////

    function allowed() {
      return policy.ifAllowed(
        {rules: [['network', 'update_policy_bandwidth_limit_rule'],
        ['network', 'update_policy_dscp_marking_rule'],
        ['network', 'update_policy_minimum_bandwidth_rule']]});
    }

    function perform(qospolicy) {
      if (qospolicy.rules.length !== 0) {
        model = {"qospolicy": qospolicy.id, "qospolicyname": qospolicy.name,
            "rules": qospolicy.rules};
        var config = {
          "title": caption,
          "submitText": caption,
          "schema": schema,
          "form": form,
          "model": model,
          "submitIcon": "pen",
          "helpUrl": basePath + "actions/rule.description.html"
        };
        return modalFormService.open(config).then(submit);
      }
      else {
        toast.add('info', interpolate(
        gettext('There are no rules to modify.')));
        return actionResultService.getActionResult()
        .result;

      }
    }

    function submit(context) {
      var id = context.model.qospolicy;
      var ruleid = [context.model.ruleid];
      var rule = context.model.rule_type;
      var data = '';

      if (rule === 'bandwidth_limit') {
        data = {direction: context.model.direction,
          max_burst_kbps: context.model.maxburstkbps,
          max_kbps: context.model.maxkbps};
        return neutronAPI.updateBandwidthRule(id, ruleid, data).then(onEditRule);
      }
      else if (rule === 'dscp_marking') {
        data = { dscp_mark: context.model.dscpmarking };
        return neutronAPI.updateDSCPMarkingRule(id, ruleid, data).then(onEditRule);
      }
      else if (rule === 'minimum_bandwidth') {
        data = {direction: context.model.direction,
          min_kbps: context.model.minkbps};
        return neutronAPI.updateMinimumBandwidthRule(id, ruleid, data).then(onEditRule);
      }
      else if (rule === 'minimum_packet_rate') {
        data = {direction: context.model.direction,
          min_kpps: context.model.minkpps};
        return neutronAPI.updateMinimumPacketRateRule(id, ruleid, data).then(onEditRule);
      }
    }

    function onEditRule(response) {
      var qosrule = response.data;
      toast.add('success', interpolate(
        gettext('Qos Policy Rule %s was successfully updated.'),[qosrule.id]));

      return actionResultService.getActionResult()
        .result;
    }

  }
})();
