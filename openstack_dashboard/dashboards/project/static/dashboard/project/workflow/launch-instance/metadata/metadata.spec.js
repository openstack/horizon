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

  describe('Launch Instance Metadata Step', function() {

    describe('metadata tree', function() {
      var $scope, $element, model;

      beforeEach(module('templates'));
      beforeEach(module('horizon.dashboard.project.workflow.launch-instance'));

      beforeEach(inject(function($injector) {
        var $compile = $injector.get('$compile');
        var $templateCache = $injector.get('$templateCache');
        var basePath = $injector.get('horizon.dashboard.project.workflow.launch-instance.basePath');
        var markup = $templateCache.get(basePath + 'metadata/metadata.html');
        model = {
          metadataDefs: { instance: false },
          novaLimits: false
        };
        $scope = $injector.get('$rootScope').$new();
        $scope.model = model;
        $element = $compile(markup)($scope);
      }));

      it('should create metadata tree only after dependencies are received', function() {
        expect($element.find('metadata-tree').length).toBe(0);

        model.metadataDefs.instance = {};
        $scope.$apply();

        expect($element.find('metadata-tree').length).toBe(0);

        model.novaLimits = {};
        $scope.$apply();

        expect($element.find('metadata-tree').length).toBe(1);
      });
    });

    describe('metadata step help', function() {
      var $scope, $element, model;

      beforeEach(module('templates'));
      beforeEach(module('horizon.dashboard.project.workflow.launch-instance'));

      beforeEach(inject(function($injector) {
        var $compile = $injector.get('$compile');
        var $templateCache = $injector.get('$templateCache');
        var basePath = $injector.get('horizon.dashboard.project.workflow.launch-instance.basePath');
        var markup = $templateCache.get(basePath + 'metadata/metadata.help.html');
        $scope = $injector.get('$rootScope').$new();
        model = {
          novaLimits: {
            maxServerMeta: null
          }
        };
        $scope.model = model;
        $element = $compile(markup)($scope);
      }));

      it('should update message based on nova limit', function() {
        expect($element.find('p+p>span').length).toBe(1);

        model.novaLimits.maxServerMeta = -1;
        $scope.$apply();

        expect($element.find('p+p>span').length).toBe(2);
        expect($element.find('p+p>span:last-child').text().trim())
          .toBe('This limit is currently not set.');

        model.novaLimits.maxServerMeta = 5;
        $scope.$apply();

        expect($element.find('p+p>span').length).toBe(2);
        expect($element.find('p+p>span:last-child').text().trim())
          .toMatch(/^This limit is currently set to/);
      });
    });
  });
})();
