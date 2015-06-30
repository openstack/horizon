/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

  describe('horizon.dashboard.project.workflow.launch-instance module', function() {

    beforeEach(module('horizon.dashboard.project'));

    it('should be defined.', function () {
      expect(angular.module('horizon.dashboard.project.workflow.launch-instance')).toBeDefined();
    });

    describe('horizon.dashboard.project.workflow.launch-instance.modal-spec', function () {
      var launchInstancedModalSpec;

      beforeEach(inject(function ($injector) {
        launchInstancedModalSpec =
          $injector.get('horizon.dashboard.project.workflow.launch-instance.modal-spec');
      }));

      it('should be defined', function () {
        expect(launchInstancedModalSpec).toBeDefined();
      });
    });

    describe('horizon.dashboard.project.workflow.launch-instance.basePath', function () {
      var basePath;

      beforeEach(module('horizon.dashboard.project'));
      beforeEach(inject(function ($injector) {
        basePath = $injector.get('horizon.dashboard.project.workflow.launch-instance.basePath');
      }));

      it('should be defined', function () {
        expect(basePath).toBeDefined();
      });

      it('should equal to "/static/dashboard/project/workflow/launch-instance/"', function () {
        expect(basePath).toEqual('/static/dashboard/project/workflow/launch-instance/');
      });
    });

  });

})();
