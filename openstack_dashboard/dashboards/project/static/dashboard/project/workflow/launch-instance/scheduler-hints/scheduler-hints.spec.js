/*
 * Copyright 2016 IBM Corp.
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

  describe('Launch Instance Scheduler Hints Step', function() {

    describe('metadata tree', function() {
      var $scope, $element, model;

      beforeEach(module('templates'));
      beforeEach(module('horizon.framework.util.i18n'));
      beforeEach(module('horizon.dashboard.project.workflow.launch-instance'));

      beforeEach(inject(function($injector) {
        var $compile = $injector.get('$compile');
        var $templateCache = $injector.get('$templateCache');
        var basePath = $injector.get('horizon.dashboard.project.workflow.launch-instance.basePath');
        var markup = $templateCache.get(basePath + 'scheduler-hints/scheduler-hints.html');
        model = {
          metadataDefs: { hints: false }
        };
        $scope = $injector.get('$rootScope').$new();
        $scope.model = model;
        $element = $compile(markup)($scope);
      }));

      it('should define display text values', function() {
        var ctrl = $element.scope().ctrl;
        expect(ctrl.text).toBeDefined();
      });

      it('should create metadata tree only after dependencies are received', function() {
        expect($element.find('metadata-tree').length).toBe(0);

        model.metadataDefs.hints = {};
        $scope.$apply();

        expect($element.find('metadata-tree').length).toBe(1);
      });
    });
  });
})();
