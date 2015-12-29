/*
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

  describe('actions directive', function () {
    var $scope, $compile, $q, $templateCache, basePath;

    var rowItem = {id: 1};
    var callback = jasmine.createSpy('callback');

    beforeEach(module('templates'));
    beforeEach(module('horizon.framework'));

    beforeEach(inject(function ($injector) {
      $compile = $injector.get('$compile');
      basePath = $injector.get('horizon.framework.widgets.basePath');
      $scope = $injector.get('$rootScope').$new();
      $q = $injector.get('$q');
      $templateCache = $injector.get('$templateCache');
    }));

    it('should have no buttons if there are no actions', function () {
      var element = batchElementFor([]);
      expect(element.children().length).toBe(0);
    });

    it('should allow for specifying action text', function () {
      var element = batchElementFor([permittedActionWithText('Create Image')]);

      expect(element.children().length).toBe(1);
      var actionList = element.find('action-list');
      expect(actionList.length).toBe(1);
      expect(actionList.attr('class').indexOf('btn-addon')).toBeGreaterThan(-1);
      expect(actionList.find('button').attr('class')).toEqual('btn btn-default btn-sm');
      expect(actionList.find('button').attr('ng-click')).toEqual('disabled || callback(item)');
      expect(actionList.text().trim()).toEqual('Create Image');

      actionList.find('button').click();
      expect(callback).toHaveBeenCalled();
    });

    it('should allow for specifying by template for create', function () {
      var element = batchElementFor([permittedActionWithType('create', 'Create Image')]);

      expect(element.children().length).toBe(1);
      var actionList = element.find('action-list');
      expect(actionList.length).toBe(1);
      expect(actionList.attr('class').indexOf('btn-addon')).toBeGreaterThan(-1);
      expect(actionList.find('button').attr('class')).toEqual('btn btn-default btn-sm pull-right');
      expect(actionList.find('button').attr('ng-click')).toEqual('disabled || callback(item)');
      expect(actionList.text().trim()).toEqual('Create Image');
    });

    it('should allow for specifying by template for delete-selected', function () {
      var element = batchElementFor([permittedActionWithType('delete-selected', 'Delete Images')]);

      expect(element.children().length).toBe(1);
      var actionList = element.find('action-list');
      expect(actionList.length).toBe(1);
      expect(actionList.attr('class').indexOf('btn-addon')).toBeGreaterThan(-1);
      expect(actionList.find('button').attr('class'))
        .toEqual('btn btn-default btn-sm btn-danger pull-right');
      expect(actionList.find('button').attr('ng-click')).toEqual('disabled || callback(item)');
      expect(actionList.text().trim()).toEqual('Delete Images');
    });

    it('should allow for specifying by template for delete', function () {
      var element = rowElementFor([permittedActionWithType('delete', 'Delete Image')]);

      expect(element.children().length).toBe(1);
      var actionList = element.find('action-list');
      expect(actionList.length).toBe(1);
      expect(actionList.attr('class').indexOf('btn-addon')).toBeGreaterThan(-1);
      expect(actionList.find('button').attr('class'))
        .toEqual('btn btn-sm pull-right btn-danger');
      expect(actionList.find('button').attr('ng-click')).toEqual('disabled || callback(item)');
      expect(actionList.text().trim()).toEqual('Delete Image');

      actionList.find('button').click();
      expect(callback).toHaveBeenCalledWith(rowItem);
    });

    it('should allow for specifying by template for danger', function () {
      var element = rowElementFor([permittedActionWithType('danger', 'Shutdown Instance')]);

      expect(element.children().length).toBe(1);
      var actionList = element.find('action-list');
      expect(actionList.length).toBe(1);
      expect(actionList.attr('class').indexOf('btn-addon')).toBeGreaterThan(-1);
      expect(actionList.find('button').attr('class'))
        .toEqual('btn btn-sm pull-right btn-danger');
      expect(actionList.find('button').attr('ng-click')).toEqual('disabled || callback(item)');
      expect(actionList.text().trim()).toEqual('Shutdown Instance');

      actionList.find('button').click();
      expect(callback).toHaveBeenCalledWith(rowItem);
    });

    it('should have one button if there is one action', function () {
      var action = getTemplatePath('action-create', getTemplate());
      var element = batchElementFor([permittedActionWithUrl(action)]);

      expect(element.children().length).toBe(1);
      var actionList = element.find('action-list');
      expect(actionList.length).toBe(1);
      expect(actionList.attr('class').indexOf('btn-addon')).toBeGreaterThan(-1);
      expect(actionList.find('button').attr('class')).toEqual('btn btn-default btn-sm btn-create');
      expect(actionList.find('button').attr('ng-click')).toEqual('disabled || callback(item)');
      expect(actionList.text().trim()).toEqual('Create Image');
    });

    it('should have no buttons if not permitted', function () {
      var element = batchElementFor([notPermittedAction()]);

      expect(element.children().length).toBe(0);
    });

    it('should have multiple buttons for multiple actions as a list', function () {
      var action1 = getTemplatePath('action-create');
      var action2 = getTemplatePath('action-delete');
      var element = batchElementFor([
        permittedActionWithUrl(action1),
        permittedActionWithUrl(action2)
      ]);

      expect(element.children().length).toBe(2);
      var actionList = element.find('action-list');
      expect(actionList.length).toBe(2);
      expect(actionList.attr('class').indexOf('btn-addon')).toBeGreaterThan(-1);
      expect(actionList.find('button.btn-create').text().trim()).toEqual('Create Image');
      expect(actionList.find('button.text-danger').text().trim()).toEqual('Delete Image');
    });

    it('should bind multiple callbacks for multiple buttons in a batch', function () {
      var callback1 = jasmine.createSpy('callback1');
      var callback2 = jasmine.createSpy('callback2');
      var element = batchElementFor([
        permittedActionWithText('Action 1', 'btn-1', callback1),
        permittedActionWithText('Action 2', 'btn-2', callback2)
      ]);

      expect(element.children().length).toBe(2);
      var actionList = element.find('action-list');
      expect(actionList.length).toBe(2);

      actionList.find('button.btn-1').click();
      expect(callback1).toHaveBeenCalled();

      actionList.find('button.btn-2').click();
      expect(callback2).toHaveBeenCalled();
    });

    it('should have as many buttons as permitted', function () {
      var actionTemplate1 = getTemplatePath('action-create');
      var element = batchElementFor([
        permittedActionWithUrl(actionTemplate1),
        notPermittedAction()
      ]);

      expect(element.children().length).toBe(1);
      var actionList = element.find('action-list');
      expect(actionList.length).toBe(1);
      expect(actionList.attr('class').indexOf('btn-addon')).toBeGreaterThan(-1);
      expect(actionList.find('button.btn-default').text().trim()).toEqual('Create Image');
    });

    it('should have multiple buttons as a dropdown with correct styling', function () {
      var element = rowElementFor([
        permittedActionWithText('Edit Instance', 'btn-custom'),
        permittedActionWithType('danger', 'Shutdown Instance')
      ]);

      expect(element.children().length).toBe(1);
      var actionList = element.find('action-list');
      expect(actionList.length).toBe(1);
      expect(actionList.attr('class').indexOf('btn-addon')).toEqual(-1);
      expect(actionList.find('button.split-button.btn-custom').text().trim())
        .toEqual('Edit Instance');
      expect(actionList.find('li a.text-danger').text().trim()).toEqual('Shutdown Instance');
    });

    it('should style danger type button as button in a dropdown', function () {
      var element = rowElementFor([
        permittedActionWithType('danger', 'Shutdown Instance'),
        permittedActionWithText('Edit Instance', 'btn-custom')
      ]);

      expect(element.children().length).toBe(1);
      var actionList = element.find('action-list');
      expect(actionList.length).toBe(1);
      expect(actionList.attr('class').indexOf('btn-addon')).toEqual(-1);
      expect(actionList.find('button.split-button.btn-danger').text().trim())
        .toEqual('Shutdown Instance');
      expect(actionList.find('li a.btn-custom').text().trim()).toEqual('Edit Instance');
    });

    it('should have multiple buttons as a dropdown for actions text', function () {
      var element = rowElementFor([
        permittedActionWithText('Create Image'),
        permittedActionWithText('Delete Image', 'text-danger')
      ]);

      expect(element.children().length).toBe(1);
      var actionList = element.find('action-list');
      expect(actionList.length).toBe(1);
      expect(actionList.attr('class').indexOf('btn-addon')).toEqual(-1);
      expect(actionList.find('button .fa').text().trim()).toEqual('Create Image');
      expect(actionList.find('li a.text-danger').text().trim()).toEqual('Delete Image');
    });

    it('should bind callbacks per button for dropdowns', function () {
      var callback1 = jasmine.createSpy('callback1');
      var callback2 = jasmine.createSpy('callback2');
      var element = rowElementFor([
        permittedActionWithText('Action 1', 'btn-1', callback1),
        permittedActionWithText('Action 2', 'btn-2', callback2)
      ]);

      expect(element.children().length).toBe(1);
      var actionList = element.find('action-list');
      expect(actionList.length).toBe(1);

      actionList.find('button .fa').click();
      expect(callback1).toHaveBeenCalledWith(rowItem);

      actionList.find('li .btn-2').click();
      expect(callback2).toHaveBeenCalledWith(rowItem);
    });

    it('should have one button if only one permitted for dropdown', function () {
      var element = rowElementFor([
        permittedActionWithText('Single Action', 'btn-custom'),
        notPermittedAction()
      ]);

      expect(element.children().length).toBe(1);
      var actionList = element.find('action-list');
      expect(actionList.length).toBe(1);
      expect(actionList.attr('class').indexOf('btn-addon')).toBeGreaterThan(-1);
      expect(actionList.find('button.btn-custom').text().trim()).toEqual('Single Action');
      expect(actionList.find('button').attr('class'))
        .toEqual('btn btn-sm pull-right btn-default btn-custom');
    });

    function permittedActionWithUrl(templateUrl) {
      return {
        template: {url: templateUrl},
        service: getService(getPermission(true), callback)
      };
    }

    function permittedActionWithText(text, actionClasses, actionCallback) {
      return {
        template: {
          text: text,
          actionClasses: actionClasses
        },
        service: getService(getPermission(true), actionCallback || callback)
      };
    }

    function permittedActionWithType(templateType, text, actioncCallback) {
      return {
        template: {
          type: templateType,
          text: text
        },
        service: getService(getPermission(true), actioncCallback || callback)
      };
    }

    function notPermittedAction() {
      return {
        template: 'dummy',
        service: getService(getPermission(false), callback)
      };
    }

    function getService(permissions, callback) {
      return {
        allowed: function(args) {
          if (args) {
            expect(args).toEqual(rowItem);
          }
          return permissions;
        },
        perform: function(args) {
          callback(args);
        }
      };
    }

    function getTemplate(templateName) {
      return $templateCache.get(getTemplatePath(templateName));
    }

    function getTemplatePath(templateName) {
      return basePath + 'action-list/' + templateName + '.mock.html';
    }

    function getPermission(allowed) {
      var deferred = $q.defer();

      if (allowed) {
        deferred.resolve();
      } else {
        deferred.reject();
      }

      return deferred.promise;
    }

    function batchElementFor(actions) {
      $scope.actions = function() {
        return actions;
      };

      var element = angular.element(getTemplate('actions.batch'));

      $compile(element)($scope);
      $scope.$apply();

      return element;
    }

    function rowElementFor(actions) {
      $scope.rowItem = rowItem;
      $scope.actions = function() {
        return actions;
      };

      var element = angular.element(getTemplate('actions.row'));

      $compile(element)($scope);
      $scope.$apply();

      return element;
    }

  });
})();
