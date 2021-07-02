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
   * @name horizon.app.core.network_qos.actions.workflow.service
   * @ngController
   *
   * @description
   * Workflow for creating network qos policy
   */

  angular
    .module('horizon.app.core.network_qos.actions')
    .factory('horizon.app.core.network_qos.actions.workflow.service', NetworkQosWorkflow);

  function NetworkQosWorkflow() {

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
          description: {
            title: gettext('Description'),
            type: 'string',
            maxLength: 255
          },
          shared: {
            title: gettext('Shared'),
            type: 'boolean',
            default: false
          }
        },
        required: ['name']
      };

      var form = [
        "name",
        {
          key: "description",
          type: "textarea"
        },
        {
          key: "shared",
          type: "checkbox"
        }
      ];

      var model = {};

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
