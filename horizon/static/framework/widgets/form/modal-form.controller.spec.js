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

  describe('modal-form controller', function () {
    var ctrl, modalInstance, context;

    beforeEach(module('horizon.framework.widgets.form'));

    beforeEach(inject(function ($controller) {
      modalInstance = {
        close: angular.noop,
        dismiss: angular.noop
      };
      context = {
        title: "title",
        form: "form",
        schema: "schema",
        model: "model"
      };
      ctrl = $controller(
        'horizon.framework.widgets.form.ModalFormController',
        {
          $modalInstance: modalInstance,
          context: context
        });
    }));

    it('sets formTitle on scope', function() {
      expect(ctrl.formTitle).toEqual('title');
    });

    it('sets form on scope', function() {
      expect(ctrl.form).toEqual('form');
    });

    it('sets schema on scope', function() {
      expect(ctrl.schema).toEqual('schema');
    });

    it('sets model on scope', function() {
      expect(ctrl.model).toEqual('model');
    });

    it('calls modalInstance close on submit', function() {
      spyOn(modalInstance, 'close');
      ctrl.submit();
      expect(modalInstance.close.calls.count()).toBe(1);
    });

    it('calls modalInstance dismiss on cancel', function() {
      spyOn(modalInstance, 'dismiss');
      ctrl.cancel();
      expect(modalInstance.dismiss.calls.count()).toBe(1);
    });
  });
}());
