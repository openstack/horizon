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
   * @name horizon.dashboard.identity.domains.actions.workflow.service
   * @ngController
   *
   * @description
   * Workflow for creating/updating domain
   */
  angular
    .module('horizon.dashboard.identity.domains.actions')
    .factory('horizon.dashboard.identity.domains.actions.workflow.service', DomainWorkflow);

  DomainWorkflow.$inject = [
    'horizon.dashboard.identity.domains.basePath'
  ];

  function DomainWorkflow(basePath) {

    var workflow = {
      init: init
    };

    function init() {
      var schema = {
        type: "object",
        properties: {
          name: {
            title: gettext('Domain Name'),
            type: 'string'
          },
          description: {
            title: gettext('Description'),
            type: 'string'
          },
          enabled: {
            title: gettext('Enabled'),
            type: 'boolean',
            default: true
          }
        },
        required: ['name']
      };

      var form = [
        {
          type: 'section',
          htmlClass: 'row',
          items: [
            {
              type: 'section',
              htmlClass: 'col-sm-6',
              items: [
                {
                  key: "name"
                },
                {
                  key: "description",
                  type: "textarea"
                },
                {
                  key: "enabled",
                  type: "radiobuttons",
                  titleMap: [
                    {value: true, name: gettext("Yes")},
                    {value: false, name: gettext("No")}
                  ]
                }
              ]
            },
            {
              type: 'template',
              templateUrl: basePath + "actions/workflow/info.help.html"
            }
          ]
        }
      ];

      var model = {
        name: "",
        description: "",
        enabled: true
      };

      var config = {
        schema: schema,
        form: form,
        model: model
      };

      return config;
    }

    return workflow;
  }
})();
