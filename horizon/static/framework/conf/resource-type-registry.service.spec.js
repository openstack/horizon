/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

  describe('resource type service', function() {
    var service;

    beforeEach(module('horizon.framework.conf'));

    beforeEach(module(function($provide) {
      $provide.value('horizon.framework.util.extensible.service', angular.noop);
    }));

    beforeEach(inject(function($injector) {
      service = $injector.get('horizon.framework.conf.resource-type-registry.service');
    }));

    it('exists', function() {
      expect(service).toBeDefined();
    });

    describe('getItemActions', function() {

      it('adds a member when called and no member present', function() {
        expect(service.getItemActions('newthing')).toBeDefined();
      });

      it('sets itemAction when getItemAction is called', function() {
        service.getItemActions('newthing').push(1);
        service.getItemActions('newthing').push(2);
        expect(service.getItemActions('newthing')).toEqual([1, 2]);
      });

    });

    describe('getBatchActions', function() {

      it('adds a member when getBatchAction is called an member not present', function() {
        expect(service.getBatchActions('newthing')).toBeDefined();
      });

      it('sets batchAction when addBatchAction is called', function() {
        service.getBatchActions('newthing').push(1);
        service.getBatchActions('newthing').push(2);
        expect(service.getBatchActions('newthing')).toEqual([1, 2]);
      });
    });

    it('returns a function that returns item actions', function() {
      service.getItemActions('newthing').push(1);
      expect(service.getItemActionsFunction('newthing')()).toEqual([1]);
    });

    it('returns a function that returns batch actions', function() {
      service.getBatchActions('newthing').push(1);
      expect(service.getBatchActionsFunction('newthing')()).toEqual([1]);
    });

    it('init calls initScope on item and batch actions', function() {
      var action = { service: { initScope: angular.noop } };
      spyOn(action.service, 'initScope');
      service.getBatchActions('newthing').push(action);
      service.initActions('newthing', { '$new': function() { return 4; }} );
      expect(action.service.initScope).toHaveBeenCalledWith(4);
    });

  });

})();
