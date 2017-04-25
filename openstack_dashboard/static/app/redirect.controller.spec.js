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

  describe('RedirectController', function() {
    var $location, $window, controller, $scope, waitSpinnerService;

    beforeEach(module('templates'));

    beforeEach(function() {
      $window = {location: { replace: jasmine.createSpy()} };

      module(function($provide) {
        $provide.value('$window', $window);
      });

      angular.module('horizon.auth', []);
      module('horizon.app');
      inject(function ($injector) {
        $location = $injector.get('$location');
        controller = $injector.get('$controller');

        var $compile = $injector.get('$compile');
        var $templateCache = $injector.get('$templateCache');
        var basePath = $injector.get('horizon.framework.widgets.basePath');

        // mock waitSpinnerService.showModalSpinner
        $scope = $injector.get('$rootScope').$new();
        waitSpinnerService =
            $injector.get('horizon.framework.widgets.modal-wait-spinner.service');

        var markup = $templateCache
            .get(basePath + 'modal-wait-spinner/modal-wait-spinner.template.html');
        var $element = angular.element(markup);
        $compile($element)($scope);
        spyOn(waitSpinnerService, 'showModalSpinner');
        $scope.$apply();

        // NOTE: This is using absUrl, so requests will already include WEBROOT.
        spyOn($location, 'absUrl').and.returnValue('path');
      });
    });

    function createController() {
      return controller('RedirectController', {});
    }

    it('should redirect the window to the location', function() {
      createController();
      expect($window.location.href).toEqual('path');
    });

    it('should start the spinner', function() {
      createController();
      expect(waitSpinnerService.showModalSpinner).toHaveBeenCalledWith('Loading');
    });

  });
})();
