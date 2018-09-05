/*
 * (c) Copyright 2016 Hewlett Packard Enterprise Development LP
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

  describe('modal-form service', function () {
    var service, $uibModal;

    beforeEach(module('horizon.framework.widgets'));
    beforeEach(module('horizon.framework.widgets.form'));

    beforeEach(inject(function ($injector, _$uibModal_) {
      $uibModal = _$uibModal_;
      service = $injector.get(
        'horizon.framework.widgets.form.ModalFormService'
      );
    }));

    it('sets open parameters to modal resolve.context', function() {
      spyOn($uibModal, 'open').and.callFake(function(config) {
        return {
          result: config
        };
      });
      var modalConfig = {
        "title": "title",
        "schema": "schema",
        "form": "form",
        "model": "model",
        "submitIcon": "icon",
        "submitText": "save",
        "helpUrl": "help.html"
      };
      var modalService = service.open(modalConfig);
      var context = modalService.resolve.context();
      expect(context.title).toEqual('title');
      expect(context.schema).toEqual('schema');
      expect(context.form).toEqual('form');
      expect(context.model).toEqual('model');
      expect(context.submitIcon).toEqual('icon');
      expect(context.submitText).toEqual('save');
      expect(context.helpUrl).toEqual('help.html');
    });

    it('sets default values for optional parameters', function() {
      spyOn($uibModal, 'open').and.callFake(function(config) {
        return {
          result: config
        };
      });
      var modalConfig = {
        "title": "title",
        "schema": "schema",
        "form": "form",
        "model": "model"
      };
      var modalService = service.open(modalConfig);
      var context = modalService.resolve.context();
      expect(context.submitIcon).toEqual('check');
      expect(context.submitText).toEqual('Submit');
    });
  });
}());
