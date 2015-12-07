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
      $scope.callback = function(item) {
        expect(item).toEqual(rowItem);
      };
      spyOn($scope, 'callback').and.callThrough();

      var element = rowElementFor([permittedActionWithType('delete', 'Delete Image')]);

      expect(element.children().length).toBe(1);
      var actionList = element.find('action-list');
      expect(actionList.length).toBe(1);
      expect(actionList.attr('class').indexOf('btn-addon')).toBeGreaterThan(-1);
      expect(actionList.find('button').attr('class')).toEqual('text-danger');
      expect(actionList.find('button').attr('ng-click')).toEqual('disabled || callback(item)');
      expect(actionList.text().trim()).toEqual('Delete Image');

      actionList.find('button').click();
      expect($scope.callback).toHaveBeenCalled();
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

    it('should have multiple buttons as a dropdown', function () {
      var action1 = getTemplatePath('action-create');
      var action2 = getTemplatePath('action-delete');

      var element = rowElementFor([
        permittedActionWithUrl(action1),
        permittedActionWithUrl(action2)
      ]);

      expect(element.children().length).toBe(1);
      var actionList = element.find('action-list');
      expect(actionList.length).toBe(1);
      expect(actionList.attr('class').indexOf('btn-addon')).toEqual(-1);
      expect(actionList.find('button .fa-user-plus').text().trim()).toEqual('Create Image');
      expect(actionList.find('li a.text-danger').text().trim()).toEqual('Delete Image');
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

    it('should have one button if only one permitted for dropdown', function () {
      var element = rowElementFor([
        permittedActionWithUrl(getTemplatePath('action-create')),
        notPermittedAction()
      ]);

      expect(element.children().length).toBe(1);
      var actionList = element.find('action-list');
      expect(actionList.length).toBe(1);
      expect(actionList.attr('class').indexOf('btn-addon')).toBeGreaterThan(-1);
      expect(actionList.find('button .fa-user-plus').text().trim()).toEqual('Create Image');
    });

    function permittedActionWithUrl(templateUrl) {
      return {
        template: {url: templateUrl},
        permissions: getPermission(true),
        callback: 'callback'
      };
    }

    function permittedActionWithText(text, actionClasses) {
      return {
        template: {
          text: text,
          actionClasses: actionClasses
        },
        permissions: getPermission(true),
        callback: 'callback'
      };
    }

    function permittedActionWithType(templateType, text) {
      return {
        template: {
          type: templateType,
          text: text
        },
        permissions: getPermission(true),
        callback: 'callback'
      };
    }

    function notPermittedAction() {
      return {template: 'dummy', permissions: getPermission(false), callback: 'callback'};
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
      $scope.actions = function(item) {
        expect(item).toEqual(rowItem);
        return actions;
      };

      var element = angular.element(getTemplate('actions.row'));

      $compile(element)($scope);
      $scope.$apply();

      return element;
    }

  });
})();
