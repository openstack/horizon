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

    function init(action, adminPassword, errorCode) {
      var errorTemplate = typeof errorCode === "string"
        ? errorCode.toLowerCase().replace(/_/g, "-") : "default";
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
          admin_password: {
            title: gettext('Admin Password'),
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
      if (adminPassword) {
        schema.required.push('admin_password');
      }

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
                  templateUrl: basePath + "actions/workflow/error." + errorTemplate + ".html",
                  condition: errorTemplate === "default"
                }
              ]
            },
            {
              type: 'section',
              htmlClass: 'col-sm-4',
              items: [
                { key: 'domain_name' },
                {
                  key: 'email',
                  condition: action === 'password'
                },
                {
                  key: 'password',
                  type: 'password',
                  condition: action === 'update'
                }
              ]
            },
            {
              type: 'section',
              htmlClass: 'col-sm-4',
              items: [
                { key: 'domain_id' },
                {
                  key: 'project',
                  type: 'select',
                  titleMap: [],
                  condition: action === 'password'
                },
                {
                  key: 'confirm',
                  type: 'password-confirm',
                  title: gettext('Confirm Password'),
                  match: 'model.password',
                  condition: action === 'update'
                }
              ]
            },
            {
              type: 'section',
              htmlClass: 'col-sm-4',
              items: [
                {
                  key: 'name',
                  readonly: action === 'password'
                },
                {
                  key: 'role',
                  type: 'select',
                  titleMap: [],
                  condition: action === 'update' || action === 'password'
                },
                {
                  key: 'admin_password',
                  type: 'password',
                  condition: !(action === 'password' && adminPassword)
                }
              ]
            },
            {
              type: 'section',
              htmlClass: 'col-sm-12',
              items: [
                {
                  key: 'description',
                  condition: action === 'password'
                },
                {
                  key: 'enabled',
                  condition: action === 'update' || action === 'password'
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
        model: model,
        size: 'md',
        helpUrl: basePath + "actions/workflow/info." + action + ".help.html"
      };

      keystone.getVersion().then(function (response) {
        var apiVersion = response.data.version;
        var domainName = config.form[0].items[1].items[0];
        var domainId = config.form[0].items[2].items[0];
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
        var projectField = config.form[0].items[2].items[1];
        projectField.titleMap = response.data.items.map(function each(item) {
          return {value: item.id, name: item.name};
        });
      });
      keystone.getRoles().then(function (response) {
        var roleField = config.form[0].items[3].items[1];
        roleField.titleMap = response.data.items.map(function each(item) {
          return {value: item.id, name: item.name};
        });
      });

      return config;
    }

    return workflow;
  }
})();
