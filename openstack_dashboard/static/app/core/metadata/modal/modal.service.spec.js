/*
 * (c) Copyright 2015 ThoughtWorks, Inc.
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
(function () {
  'use strict';

  describe('horizon.app.core.metadata.modal', function() {

    describe('service.modalservice', function() {
      var modalService, metadataService, $uibModal;

      beforeEach(module('ui.bootstrap', function($provide) {
        $uibModal = jasmine.createSpyObj('$uibModal', ['open']);

        $provide.value('$uibModal', $uibModal);
      }));

      beforeEach(module('horizon.app.core', function($provide) {
        $provide.constant('horizon.app.core.basePath', '/a/sample/path/');
      }));

      beforeEach(module('horizon.app.core.metadata', function($provide) {
        metadataService = jasmine.createSpyObj('metadataService', ['getMetadata', 'getNamespaces']);
        $provide.value('horizon.app.core.metadata.service', metadataService);
      }));

      beforeEach(module('horizon.app.core.metadata.modal'));

      beforeEach(inject(function($controller, $injector) {
        modalService = $injector.get('horizon.app.core.metadata.modal.service');
      }));

      it('should define service.open()', function() {
        expect(modalService.open).toBeDefined();
      });

      it('should invoke $uibModal.open with correct params', function() {
        modalService.open('resource', 'id');

        expect($uibModal.open).toHaveBeenCalled();

        var args = $uibModal.open.calls.argsFor(0)[0];
        expect(args.templateUrl).toEqual('/a/sample/path/metadata/modal/modal.html');
        expect(args.resolve.params()).toEqual({resource: 'resource', id: 'id'});
      });

    });
  });

})();
