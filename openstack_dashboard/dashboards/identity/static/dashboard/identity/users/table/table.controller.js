/**
 * Copyright 2015 IBM Corp.
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
   * @ngdoc identityUsersTableController
   * @ngController
   *
   * @description
   * Controller for the identity users table.
   * Serve as the focal point for table actions.
   */
  angular
    .module('horizon.dashboard.identity.users')
    .controller('identityUsersTableController', identityUsersTableController);

  identityUsersTableController.$inject = [
    'horizon.framework.widgets.toast.service',
    'horizon.framework.util.i18n.gettext',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.app.core.openstack-service-api.keystone'
  ];

  function identityUsersTableController(toast, gettext, policy, keystone) {

    var ctrl = this;
    ctrl.users = [];
    ctrl.iusers = [];
    ctrl.userSession = {};
    ctrl.checked = {};

    init();

    ////////////////////////////////

    function init() {
      // if user has permission
      // fetch table data and populate it
      var rules = [['identity', 'identity:list_users']];
      policy.ifAllowed({ rules: rules }).then(policySuccess, policyFailed);
    }

    function policySuccess() {
      keystone.getUsers().success(getUsersSuccess);
      keystone.getCurrentUserSession().success(getSessionSuccess);
    }

    function policyFailed() {
      var msg = gettext('Insufficient privilege level to view user information.');
      toast.add('warning', msg);
    }

    function getUsersSuccess(response) {
      ctrl.users = response.items;
    }

    function getSessionSuccess(response) {
      ctrl.userSession = response;
    }
  }

})();
