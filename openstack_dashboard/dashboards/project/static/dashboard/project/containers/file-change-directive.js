/*
 *    (c) Copyright 2015 Rackspace US, Inc
 *
 * Licensed under the Apache License, Version 2.0 (the 'License');
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an 'AS IS' BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function () {
  'use strict';

  angular
    .module('horizon.dashboard.project.containers')
    .directive('onFileChange', OnFileChange);

  OnFileChange.$inject = [];

  function OnFileChange() {
    return {
      restrict: 'A',
      require: 'ngModel',
      link: function link(scope, element, attrs, ngModel) {
        var onFileChangeHandler = scope.$eval(attrs.onFileChange);
        element.on('change', function change(event) {
          onFileChangeHandler(event.target.files);
          // we need to manually change the view element and force a render
          // to have angular pick up that the file upload now has a value
          // and any required constraint is now satisfied
          scope.$apply(function expression() {
            ngModel.$setViewValue(event.target.files[0].name);
            ngModel.$render();
          });
        });
      }
    };
  }
})();
