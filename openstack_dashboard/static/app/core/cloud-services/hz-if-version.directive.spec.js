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

  describe('horizon.app.core.cloud-services.hzIfApiVersion', function() {

    function fakeAPI() {
      return {
        then: function(callback) {
          var actual = { data: { version: 3 } };
          callback(actual);
        }
      };
    }

    var $compile, $scope, keystoneAPI;

    var $mockHtmlInput = '$mock-input';
    var baseHtml = [
      '<div>',
      '<div hz-if-api-version=\'$mock-input\'>',
      '<div class="child-element">',
      '</div>',
      '</div>',
      '</div>'
    ].join('');

    ///////////////////////

    beforeEach(module('horizon.app.core.openstack-service-api'));
    beforeEach(module('horizon.app.core.cloud-services'));
    beforeEach(module('horizon.framework.conf'));
    beforeEach(module('horizon.framework.util.http'));
    beforeEach(module('horizon.framework.util.promise-toggle'));
    beforeEach(module('horizon.framework.widgets.toast'));

    beforeEach(inject(function($injector) {
      keystoneAPI = $injector.get('horizon.app.core.openstack-service-api.keystone');
      spyOn(keystoneAPI, 'getVersion').and.callFake(fakeAPI);
    }));

    beforeEach(inject(function($injector) {
      $compile = $injector.get('$compile');
      $scope = $injector.get('$rootScope');
    }));

    it('should evaluate child elements when version is correct', function () {
      var params = '{\"keystone\": 3}';
      var template = baseHtml.replace($mockHtmlInput, params);
      var element = $compile(template)($scope);
      expect(element.children().length).toBe(0);

      $scope.$apply();
      expect(element.children().length).toBe(1);
    });

    it('should not evaluate child elements when version is wrong', function () {
      var params = '{\"keystone\": 1}';
      var template = baseHtml.replace($mockHtmlInput, params);
      var element = $compile(template)($scope);
      expect(element.children().length).toBe(0);

      $scope.$apply();
      expect(element.children().length).toBe(0);
    });

    it('should evaluate child elements when version <= given value', function () {
      var params = '{\"keystone\": 4, \"operator\": \"<\"}';
      var template = baseHtml.replace($mockHtmlInput, params);
      var element = $compile(template)($scope);
      expect(element.children().length).toBe(0);

      $scope.$apply();
      expect(element.children().length).toBe(1);
    });

    it('should evaluate child elements when version < given value', function () {
      var params = '{\"keystone\": 4, \"operator\": \"<\"}';
      var template = baseHtml.replace($mockHtmlInput, params);
      var element = $compile(template)($scope);
      expect(element.children().length).toBe(0);

      $scope.$apply();
      expect(element.children().length).toBe(1);
    });

    it('should NOT evaluate child elements when version != given value', function () {
      var params = '{\"keystone\": 4, \"operator\": \"==\"}';
      var template = baseHtml.replace($mockHtmlInput, params);
      var element = $compile(template)($scope);
      expect(element.children().length).toBe(0);

      $scope.$apply();
      expect(element.children().length).toBe(0);
    });

    it('should evaluate child elements when version > given value', function () {
      var params = '{\"keystone\": 4, \"operator\": \">\"}';
      var template = baseHtml.replace($mockHtmlInput, params);
      var element = $compile(template)($scope);
      expect(element.children().length).toBe(0);

      $scope.$apply();
      expect(element.children().length).toBe(0);
    });

    it('should evaluate child elements when version >= given value', function () {
      var params = '{\"keystone\": 3, \"operator\": \">=\"}';
      var template = baseHtml.replace($mockHtmlInput, params);
      var element = $compile(template)($scope);
      expect(element.children().length).toBe(0);

      $scope.$apply();
      expect(element.children().length).toBe(1);
    });

    it('should NOT evaluate child elements when operator attr is wrong', function () {
      var params = '{\"keystone\": 3, \"operator\": \"hi\"}';
      var template = baseHtml.replace($mockHtmlInput, params);
      var element = $compile(template)($scope);
      expect(element.children().length).toBe(0);

      $scope.$apply();
      expect(element.children().length).toBe(0);
    });

    it('should NOT evaluate child elements when attrs are wrong', function () {
      var params = '{\"pine\": \"apple\"}';
      var template = baseHtml.replace($mockHtmlInput, params);
      var element = $compile(template)($scope);
      expect(element.children().length).toBe(0);

      $scope.$apply();
      expect(element.children().length).toBe(0);
    });

  });
})();
