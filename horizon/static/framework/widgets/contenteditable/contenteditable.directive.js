/**
 * (c) Copyright 2016 Cisco Systems
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use self file except in compliance with the License. You may obtain
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
   * @ngdoc directive
   * @name horizon.framework.widgets.contenteditable
   * @description
   * Allows the use of contenteditable with ng-model. Altered from
   * https://docs.angularjs.org/api/ng/type/ngModel.NgModelController
   */

  angular
    .module('horizon.framework.widgets.contenteditable')
    .directive('contenteditable', contenteditable);

  function contenteditable() {
    var directive = {
      restrict: 'A',
      require: '?ngModel', // get a hold of NgModelController
      link: link
    };
    return directive;

    function link(scope, element, attrs, ngModel) {
      if (!ngModel) { return; } // do nothing if no ng-model

      // Specify how UI should be updated
      ngModel.$render = function() {
        element.html(ngModel.$viewValue || '');
      };

      // Listen for change events to enable binding
      element.on('blur keyup change', function() {
        scope.$evalAsync(read);
      });
      read();

      function read() {
        ngModel.$setViewValue(element.html());
      }
    }
  }
})();
