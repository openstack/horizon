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
   * @name horizon.app.core.keypairs.create.service
   * @description Service for the key pair create modal
   */
  angular
    .module('horizon.app.core.keypairs.actions')
    .factory('horizon.app.core.keypairs.actions.create.service', createService);

  createService.$inject = [
    'horizon.app.core.keypairs.basePath',
    'horizon.app.core.keypairs.resourceType',
    'horizon.app.core.openstack-service-api.nova',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.util.file.text-download',
    'horizon.framework.widgets.form.ModalFormService',
    'horizon.framework.widgets.toast.service'
  ];

  function createService(
    basePath, resourceType, nova, policy, actionResult, download, modal, toast
  ) {

    var keypairs = [];
    var caption = gettext("Create Key Pair");
    var invalidMsg = gettext("Key pair already exists.");

    // schema
    var schema = {
      type: "object",
      properties: {
        "name": {
          title: gettext("Key Pair Name"),
          type: "string",
          pattern: "^[A-Za-z0-9 -_]+$"
        },
        "key_type": {
          title: gettext("Key Type"),
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
                templateUrl: basePath + "actions/create.key-type.html"
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
      allowed: allowed,
      getKeypairs: getKeypairs
    };

    return service;

    //////////////

    function allowed() {
      return policy.ifAllowed({ rules: [['compute', 'os_compute_api:os-keypairs:create']] });
    }

    function perform() {
      getKeypairs();
      model = { key_type: 'ssh' };
      var config = {
        "title": caption,
        "submitText": caption,
        "schema": schema,
        "form": form,
        "model": model,
        "submitIcon": "plus",
        "size": "md",
        "helpUrl": basePath + "actions/create.description.html"
      };
      return modal.open(config).then(submit);
    }

    function submit(context) {
      return nova.createKeypair(context.model).then(success);
    }

    /**
     * @ngdoc function
     * @name success
     * @description
     * Informs the user about the created key pair.
     * @param {Object} keypair The new key pair object
     * @returns {undefined} No return value
     */
    function success(response) {
      var successMsg = gettext('Key pair %(name)s was successfully created.');
      toast.add('success', interpolate(successMsg, { name: response.data.name }, true));
      download.downloadTextFile(response.data.private_key, response.data.name + '.pem');
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
