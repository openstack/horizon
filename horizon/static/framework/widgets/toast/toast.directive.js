/*
 * Copyright 2015 IBM Corp.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
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
    * @ngdoc directive
    * @name horizon.framework.widgets.toast.directive:toast
    *
    * @description
    * The `toast` directive allows you to place the toasts wherever you
    * want in your layout. Currently styling is pulled from Bootstrap alerts.
    *
    * @restrict EA
    * @scope true
    *
    */
  angular
    .module('horizon.framework.widgets.toast')
    .directive('toast', toast);

  toast.$inject = ['horizon.framework.widgets.toast.service',
                   'horizon.framework.widgets.basePath'];

  function toast(toastService, path) {

    var directive = {
      restrict: 'EA',
      templateUrl: path + 'toast/toast.html',
      scope: {},
      link: link
    };

    return directive;

    function link(scope) {
      scope.toast = toastService;
    }
  }

})();
