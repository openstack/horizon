/**
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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
(function () {
  'use strict';

  function digestMarkup(scope, compile, markup) {
    var element = angular.element(markup);
    compile(element)(scope);

    scope.$apply();
    return element;
  }

  describe('detailHeader', function () {
    var $scope, $compile;

    beforeEach(module('templates'));
    beforeEach(module('horizon.framework'));

    beforeEach(inject(function ($injector) {
      $compile = $injector.get('$compile');
      $scope = $injector.get('$rootScope').$new();
    }));

    it('defines basic elements', function () {
      var markup = '<hz-page-header header="A Title" ' +
        'description="A Description"><a href="#">A href</a></hz-page-header>';

      var $element = digestMarkup($scope, $compile, markup);

      expect($element).toBeDefined();
      expect($element.find('.page-header').length).toBe(1);
      expect($element.find('h1').length).toBe(1);
      expect($element.find('h1').text()).toBe('A Title');
      expect($element.find('p').length).toBe(1);
      expect($element.find('p').text()).toBe('A Description');
      expect($element.find('a').length).toBe(1);
      expect($element.find('a').text()).toBe('A href');
    });

  });

})();
