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

  describe('hz.dashboard.launch-instance module', function() {

    beforeEach(module('hz.dashboard'));

    it('should be defined.', function () {
      expect(angular.module('hz.dashboard.launch-instance')).toBeDefined();
    });

    describe('hz.dashboard.launch-instance.modal-spec', function () {
      var launchInstancedModalSpec;

      beforeEach(inject(function ($injector) {
        launchInstancedModalSpec = $injector.get('hz.dashboard.launch-instance.modal-spec');
      }));

      it('should be defined', function () {
        expect(launchInstancedModalSpec).toBeDefined();
      });
    });
  });

})();
