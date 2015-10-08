/*
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
(function() {
  'use strict';

  describe('horizon.framework.util.tech-debt.helper-functions', function () {
    beforeEach(function () {
      angular.mock.module('horizon.framework.util.tech-debt');
    });

    var hzUtils;
    beforeEach(function () {
      angular.mock.inject(function ($injector) {
        hzUtils = $injector.get('horizon.framework.util.tech-debt.helper-functions');
      });
    });

    describe('loadAngular', function () {
      var rootScope, element;

      beforeEach(function () {
        element = angular.element('<div>');

        angular.mock.inject(function ($injector) {
          rootScope = $injector.get('$rootScope');
        });
        spyOn(rootScope, '$apply');
      });

      it('should call a compile and apply ', function () {
        hzUtils.loadAngular(element);
        //checks the use of apply function
        expect(rootScope.$apply).toHaveBeenCalled();
        //checks the use of compile function
        expect(element.hasClass('ng-scope')).toBeTruthy();
      });
    });
  });
})();
