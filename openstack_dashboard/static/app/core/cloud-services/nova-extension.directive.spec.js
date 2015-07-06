/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

  describe('horizon.app.core.cloud-services', function () {

    describe('directive:novaExtension', function () {
      var $timeout, $scope, element, html;
      html = [
            '<nova-extension required-extensions=\'["config_drive"]\'>',
              '<div class="child-element">',
              '</div>',
            '</nova-extension>'
          ].join('');

      beforeEach(module('horizon.app.core.cloud-services', function ($provide) {
        $provide.value('horizon.app.core.cloud-services.ifFeaturesEnabled', function () {
          return {
            then: function (successCallback) {
              $timeout(successCallback);
            }
          };
        });
      }));

      beforeEach(inject(function ($injector) {
        var $compile = $injector.get('$compile');
        $scope = $injector.get('$rootScope').$new();
        $timeout = $injector.get('$timeout');
        element = $compile(html)($scope);
      }));

      it('should be compiled', function () {
        expect(element.hasClass('ng-scope')).toBe(true);
      });

      it('should have class name `ng-hide` by default', function () {
        expect(element.hasClass('ng-hide')).toBe(true);
      });

      it('should have no class name `ng-hide` after an asyncs callback', function () {
        $timeout(function () {
          expect(element.hasClass('ng-hide')).toBe(false);
        });
        $timeout.flush();
      });

      it('should have the right child element', function () {
        expect(element.children().first().hasClass('child-element')).toBe(true);
      });
    });
  });

})();
