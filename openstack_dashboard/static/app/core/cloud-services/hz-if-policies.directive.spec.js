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

(function () {
  'use strict';

  describe('horizon.app.core.cloud-services.hzIfPolicies', function () {

    var $scope, deferred, element;
    var policyService = {
      ifAllowed: function() {
        return deferred.promise;
      }
    };

    var template = [
      '<div>',
      '<div hz-if-policies=\'\"policy_rules\"\'>',
      '<div class="child-element"></div>',
      '</div>',
      '</div>'
    ].join('');

    beforeEach(module('horizon.app.core.cloud-services'));
    beforeEach(module('horizon.framework.util.promise-toggle'));

    beforeEach(module(function($provide) {
      var factoryName = 'horizon.app.core.openstack-service-api.policy';
      $provide.value(factoryName, policyService);
      spyOn(policyService, 'ifAllowed').and.callThrough();
    }));

    beforeEach(inject(function($injector) {
      var $compile = $injector.get('$compile');
      $scope = $injector.get('$rootScope');
      deferred = $injector.get('$q').defer();
      element = $compile(template)($scope);
    }));

    //////////////

    it('should evaluate child elements if policies are allowed', allowed);
    it('should not evaluate child elements if policies are not allowed', notAllowed);

    //////////////

    function allowed() {
      expect(element.children().length).toBe(0);
      expect(policyService.ifAllowed).toHaveBeenCalledWith('policy_rules');

      deferred.resolve();
      $scope.$apply();
      expect(element.children().length).toBe(1);
    }

    function notAllowed() {
      expect(element.children().length).toBe(0);
      expect(policyService.ifAllowed).toHaveBeenCalledWith('policy_rules');

      deferred.reject();
      $scope.$apply();
      expect(element.children().length).toBe(0);
    }

  }); // end of hzIfPolicies
})(); // end of IIFE
