/*
 * (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP
 *
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

(function () {
  'use strict';

  angular
    .module('horizon.framework.widgets', [
      'horizon.framework.widgets.headers',
      'horizon.framework.widgets.details',
      'horizon.framework.widgets.help-panel',
      'horizon.framework.widgets.wizard',
      'horizon.framework.widgets.table',
      'horizon.framework.widgets.modal',
      'horizon.framework.widgets.modal-wait-spinner',
      'horizon.framework.widgets.transfer-table',
      'horizon.framework.widgets.charts',
      'horizon.framework.widgets.action-list',
      'horizon.framework.widgets.metadata',
      'horizon.framework.widgets.toast',
      'horizon.framework.widgets.magic-search',
      'horizon.framework.widgets.load-edit'
    ])
    .config(config);

  config.$inject = ['$provide', '$windowProvider'];

  function config($provide, $windowProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'framework/widgets/';
    $provide.constant('horizon.framework.widgets.basePath', path);
  }

})();
