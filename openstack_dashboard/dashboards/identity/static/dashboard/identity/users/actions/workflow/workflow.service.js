/**
 * Copyright 2017 NEC Corporation
 *
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
   * @name horizon.dashboard.identity.users.actions.workflow.service
   * @ngController
   *
   * @description
   * Workflow for creating/updating user
   */
  angular
    .module('horizon.dashboard.identity.users.actions')
    .factory('horizon.dashboard.identity.users.actions.workflow.service', UserWorkflow);

  UserWorkflow.$inject = [
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.dashboard.identity.users.basePath'
  ];

  function UserWorkflow(keystone, basePath) {

    var workflow = {
      init: init
    };

    function init(action) {
      var schema = {
        type: 'object',
        properties: {
          domain_name: {
            title: gettext('Domain Name'),
            type: 'string',
            readOnly: true
          },
          domain_id: {
            title: gettext('Domain Id'),
            type: 'string',
            readOnly: true
          },
          name: {
            title: gettext('User Name'),
            type: 'string'
          },
          email: {
            title: gettext('Email'),
            type: 'string'
          },
          password: {
            title: gettext('Password'),
            type: 'string'
          },
          project: {
            title: gettext('Primary Project'),
            type: 'string'
          },
          role: {
            title: gettext('Role'),
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
        required: ['name', 'password', 'project', 'role', 'enabled']
      };

      var form = [
        {
          type: 'section',
          htmlClass: 'row',
          items: [
            {
              type: 'section',
              htmlClass: 'col-sm-12',
              items: [
                {
                  type: 'template',
                  templateUrl: basePath + "actions/workflow/info." + action + ".help.html"
                },
                { key: 'domain_name' },
                { key: 'domain_id' },
                { key: 'name' },
                { key: 'email' },
                {
                  key: 'password',
                  type: 'password',
                  condition: action === 'update'
                },
                {
                  key: 'confirm',
                  type: 'password-confirm',
                  title: 'Confirm Password',
                  match: 'model.password',
                  condition: action === 'update'
                },
                {
                  key: 'project',
                  type: 'select',
                  titleMap: []
                },
                {
                  key: 'role',
                  type: 'select',
                  titleMap: [],
                  condition: action === 'update'
                },
                { key: 'description' },
                {
                  key: 'enabled',
                  condition: action === 'update'
                }
              ]
            }
          ]
        }
      ];

      var model = {};

      var config = {
        schema: schema,
        form: form,
        model: model
      };

      keystone.getVersion().then(function (response) {
        var apiVersion = response.data.version;
        var domainName = config.form[0].items[0].items[1];
        var domainId = config.form[0].items[0].items[2];
        if (apiVersion !== "3") {
          domainName.condition = true;
          domainId.condition = true;
        }
        return apiVersion;
      });
      keystone.getDefaultDomain().then(function (response) {
        config.model.domain_name = response.data.name;
        config.model.domain_id = response.data.id;
        return response.data;
      });
      keystone.getProjects().then(function (response) {
        var projectField = config.form[0].items[0].items[7];
        projectField.titleMap = response.data.items.map(function each(item) {
          return {value: item.id, name: item.name};
        });
      });
      keystone.getRoles().then(function (response) {
        var roleField = config.form[0].items[0].items[8];
        roleField.titleMap = response.data.items.map(function each(item) {
          return {value: item.id, name: item.name};
        });
      });

      return config;
    }

    return workflow;
  }
})();
