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
  * @ngname horizon.app.core.network_qos.actions.add-rule.service
  *
  * @description
  * Provides all of the actions for creating rule to a network qos policy.
  */

  angular
    .module('horizon.app.core.network_qos')
    .factory('horizon.app.core.network_qos.actions.add-rule.service', addRuleService);

  addRuleService.$inject = [
    'horizon.app.core.openstack-service-api.neutron',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.app.core.network_qos.resourceType',
    'horizon.framework.widgets.form.ModalFormService',
    'horizon.framework.widgets.toast.service',
    'horizon.framework.util.actions.action-result.service',
    'horizon.app.core.network_qos.basePath'
  ];

  function addRuleService(
    neutronAPI,
    policy,
    resourceType,
    modal,
    toast,
    actionResultService,
    basePath
  ) {

    var caption = gettext("Add Rule");

    // schema
    var schema = {
      type: "object",
      properties: {
        qospolicy: {
          title: gettext('QoS Policy Id'),
          type: 'string',
          readOnly: true
        },
        qospolicyname: {
          title: gettext('QoS Policy Name'),
          type: 'string',
          readOnly: true
        },
        type: {
          title: gettext('Type'),
          type: 'string',
          enum: ['bandwidth_limit', 'dscp_marking', 'minimum_bandwidth', 'minimum_packet_rate']
        }
      },
      required: ['type']
    };

    // form
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
                templateUrl: basePath + "actions/add-rule.html"
              }
            ]
          }
        ]
      }
    ];

    // model
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
        {rules: [['network', 'create_policy_dscp_marking_rule'],
        ['network', 'create_policy_minimum_bandwidth_rule'],
        ['network', 'create_policy_bandwidth_limit_rule']]});
    }

    function perform(qospolicy) {
      model = {"qospolicy": qospolicy.id, "qospolicyname": qospolicy.name};
      var config = {
        "title": caption,
        "submitText": caption,
        "schema": schema,
        "form": form,
        "model": model,
        "submitIcon": "plus",
        "helpUrl": basePath + "actions/rule.description.html"
      };
      return modal.open(config).then(submit);
    }

    function submit(context) {
      var id = context.model.qospolicy;
      var data = {};
      if (context.model.rule_type === 'dscp_marking') {
        data = {
          dscp_mark: context.model.dscpmarking
        };
        return neutronAPI.createDSCPMarkingRule(id, data).then(onAddRule);
      }
      else if (context.model.rule_type === 'minimum_bandwidth') {
        data = {
          direction: context.model.direction,
          min_kbps: context.model.minkbps
        };
        return neutronAPI.createMinimumBandwidthRule(id, data).then(onAddRule);
      }
      else if (context.model.rule_type === 'bandwidth_limit') {
        var direction = context.model.direction !== undefined
                      ? context.model.direction : 'egress';
        data = {
          direction: direction,
          max_burst_kbps: context.model.maxburstkbps,
          max_kbps: context.model.maxkbps
        };
        return neutronAPI.createBandwidthLimitRule(id, data).then(onAddRule);
      }
      else if (context.model.rule_type === 'minimum_packet_rate') {
        data = {
          direction: context.model.direction,
          min_kpps: context.model.minkpps
        };
        return neutronAPI.createMinimumPacketRateRule(id, data).then(onAddRule);
      }
    }

    /**
     * @ngdoc function
     * @name onAddRule
     * @description
     * Informs the user about the added rule.
     */

    function onAddRule(response) {
      var ruleRes = response.data;
      toast.add('success', interpolate('QoS Policy Rule successfully created'));

      return actionResultService.getActionResult()
        .created(resourceType, ruleRes.id)
        .result;
    }

  }
})();

