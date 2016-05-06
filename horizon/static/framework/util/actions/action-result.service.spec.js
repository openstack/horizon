/*
 * (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP
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

  describe('horizon.framework.util.actions.action-result.service', function() {
    var service;

    beforeEach(module('horizon.framework.util.actions'));

    beforeEach(inject(function($injector) {
      service = $injector.get('horizon.framework.util.actions.action-result.service');
    }));

    describe('getIdsOfType', function() {

      it('returns an empty array if no items', function() {
        expect(service.getIdsOfType([], 'OS::Glance::Image')).toEqual([]);
      });

      it('returns an empty array if items is falsy', function() {
        expect(service.getIdsOfType(false, 'OS::Glance::Image')).toEqual([]);
      });

      it('returns items with matching type', function() {
        var items = [{type: 'No::Match'}, {type: 'OS::Glance::Image', id: 1},
          {type: 'OS::Glance::Image', id: 2}];
        expect(service.getIdsOfType(items, 'OS::Glance::Image')).toEqual([1, 2]);
      });
    });

    it('has getActionResult', function() {
      expect(service.getActionResult).toBeDefined();
    });

    describe('ActionResult', function() {
      var actionResult;
      var type = 'OS::Nova::Server';
      var id = 'the-id-value';

      beforeEach(function() {
        actionResult = service.getActionResult();
      });

      it('.updated() adds updated items', function() {
        actionResult.updated(type, id);
        expect(actionResult.result.updated)
          .toEqual([{type: 'OS::Nova::Server', id: 'the-id-value'}]);
      });

      it('.created() adds created items', function() {
        actionResult.created(type, id);
        expect(actionResult.result.created)
          .toEqual([{type: 'OS::Nova::Server', id: 'the-id-value'}]);
      });

      it('.deleted() adds deleted items', function() {
        actionResult.deleted(type, id);
        expect(actionResult.result.deleted)
          .toEqual([{type: 'OS::Nova::Server', id: 'the-id-value'}]);
      });

      it('.failed() adds failed items', function() {
        actionResult.failed(type, id);
        expect(actionResult.result.failed)
          .toEqual([{type: 'OS::Nova::Server', id: 'the-id-value'}]);
      });

    });

  });

})();
