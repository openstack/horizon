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
   * @ngdoc overview
   * @name horizon.app.core.keypairs.import.service
   * @description Service for the key pair import modal
   */
  angular
    .module('horizon.app.core.keypairs.actions')
    .factory('horizon.app.core.keypairs.actions.import.service', importService);

  importService.$inject = [
    'horizon.app.core.keypairs.basePath',
    'horizon.app.core.keypairs.resourceType',
    'horizon.app.core.openstack-service-api.nova',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.widgets.form.ModalFormService',
    'horizon.framework.widgets.toast.service'
  ];

  function importService(
    basePath, resourceType, nova, policy, actionResult, modal, toast
  ) {

    var keypairs = [];
    var caption = gettext("Import Public Key");
    var invalidMsg = gettext("Key pair already exists.");

    // schema
    var schema = {
      type: "object",
      properties: {
        "name": {
          title: gettext("Key Pair Name"),
          type: "string",
          pattern: "^[A-Za-z0-9 _-]+$"
        },
        "key_type": {
          title: gettext("Key Type"),
          type: "string"
        },
        "public_key": {
          title: gettext("Public Key"),
          type: "string"
        }
      }
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
                key: "name",
                validationMessage: {
                  keypairExists: invalidMsg
                },
                $validators: {
                  keypairExists: function (name) {
                    return (keypairs.indexOf(name) === -1);
                  }
                },
                required: true
              },
              {
                type: "template",
                templateUrl: basePath + "actions/import.public-key.html"
              }
            ]
          }
        ]
      }
    ];

    // model
    var model;

    var service = {
      perform: perform,
      allowed: allowed
    };

    return service;

    //////////////

    function allowed() {
      return policy.ifAllowed({ rules: [['compute', 'os_compute_api:os-keypairs:create']] });
    }

    function perform() {
      getKeypairs();
      model = {
        key_type: "ssh",
        public_key: ""
      };
      var config = {
        "title": caption,
        "submitText": caption,
        "schema": schema,
        "form": form,
        "model": model,
        "submitIcon": "upload",
        "size": "md",
        "helpUrl": basePath + "actions/import.description.html"
      };
      return modal.open(config).then(submit);
    }

    function submit(context) {
      return nova.createKeypair(context.model).then(success);
    }

    function success(response) {
      var successMsg = gettext('Successfully imported key pair %(name)s.');
      toast.add('success', interpolate(successMsg, { name: response.data.name }, true));
      var result = actionResult.getActionResult().created(resourceType, response.data.name);
      return result.result;
    }

    function getKeypairs() {
      nova.getKeypairs().then(function(response) {
        keypairs = response.data.items.map(getName);
      });
    }

    function getName(item) {
      return item.keypair.name;
    }
  }
})();
