/*
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

  angular
    .module('horizon.framework.widgets.action-list')
    .factory('horizon.framework.widgets.action-list.actions.service', actionsService);

  actionsService.$inject = [
    '$compile',
    '$http',
    '$parse',
    '$q',
    '$templateCache',
    'horizon.framework.widgets.basePath',
    'horizon.framework.util.q.extensions'
  ];

  function actionsService(
    $compile,
    $http,
    $parse,
    $q,
    $templateCache,
    basePath,
    $qExtensions
  ) {
    return function(spec) {
      return createService(
        spec.scope,
        spec.element,
        spec.ctrl,
        spec.listType,
        spec.item);
    };

    ///////////////

    function createService(scope, element, ctrl, listType, item) {
      var service = {
        renderActions: renderActions
      };

      return service;

      function renderActions(allowedActions) {
        allowedActions.forEach(function(allowedAction) {
          allowedAction.promise = getPermissions(allowedAction);
          allowedAction.context = allowedAction;
        });

        $qExtensions.allSettled(allowedActions).then(renderPermittedActions);

        function getPermissions(allowedAction) {
          if (listType === 'batch') {
            return allowedAction.service.allowed();
          } else {
            var itemVal = $parse(item)(scope);
            return allowedAction.service.allowed(itemVal);
          }
        }
      }

      /**
       * Render permitted actions as per the list type
       */
      function renderPermittedActions(permittedActions) {

        if (permittedActions.pass.length > 0) {
          var templateFetch = $q.all(permittedActions.pass.map(getTemplate));

          if (listType === 'batch' || permittedActions.pass.length === 1) {
            element.addClass('btn-addon');
            templateFetch.then(addButtons);
          } else {
            templateFetch.then(addDropdown);
          }
        }
      }

      /**
       * Add all the buttons as a list of buttons
       */
      function addButtons(templates) {
        templates.forEach(addTemplate);
      }

      /**
       * Add the button template as a button
       */
      function addTemplate(template) {
        element.append(renderButton(template, scope));
      }

      /**
       * Add all the buttons as a dropdown button group
       */
      function addDropdown(templates) {
        var splitButton = getSplitButton(templates[0]);
        var actionList = [];

        for (var iCnt = 1; iCnt < templates.length; iCnt++) {
          actionList.push(getMenuButton(templates[iCnt]));
        }

        var actionListElem = renderList(actionList, splitButton, scope);
        element.append($compile(actionListElem)(scope));
      }

      /**
       * Render buttons each inside the <action-list> element
       */
      function renderButton(actionTemplate, scope) {
        var actionElement = angular.element(actionTemplate.template);
        actionElement.attr('callback', actionTemplate.callback);

        var actionListElem = angular.element('<action-list>');
        actionListElem.addClass('btn-addon');
        actionListElem.append(actionElement);

        return $compile(actionListElem)(scope);
      }

      /**
       * Render buttons inside a single <action-list> element
       * with the first being a `split-button` and the rest as
       * `menu-item` buttons
       */
      function renderList(actionList, splitButton, scope) {
        var actionListElem = angular.element('<action-list>');
        actionListElem.attr('dropdown', 'true');
        actionListElem.append(splitButton);
        actionListElem.append(getMenu(actionList, scope));
        return actionListElem;
      }

      /**
       * Get the HTML for a `split-button`
       */
      function getSplitButton(actionTemplate) {
        var actionElement = angular.element(actionTemplate.template);
        actionElement.attr('button-type', 'split-button');
        actionElement.attr('action-classes', actionElement.attr('action-classes'));
        actionElement.attr('callback', actionTemplate.callback);
        return actionElement;
      }

      /**
       * Get the HTML for a `menu`
       */
      function getMenu(actionList) {
        var menuElem = angular.element('<menu>');
        menuElem.append(actionList);
        return menuElem;
      }

      /**
       * Get the HTML for a `menu-item` button
       */
      function getMenuButton(actionTemplate) {
        var actionElement = angular.element(actionTemplate.template);
        actionElement.attr('button-type', 'menu-item');
        actionElement.attr('callback', actionTemplate.callback);
        return actionElement;
      }

      /**
       * Fetch the HTML Template for the Action
       */
      function getTemplate(permittedAction, index, permittedActions) {
        var defered = $q.defer();
        var action = permittedAction.context;
        $http.get(getTemplateUrl(action, permittedActions.length), {cache: $templateCache})
          .then(onTemplateGet);
        return defered.promise;

        function onTemplateGet(response) {
          var callback = ctrl.generateDynamicCallback(action.service, index);
          var template = response.data
                .replace(
                  '$action-classes$', getActionClasses(action, index, permittedActions.length)
                )
                .replace('$text$', action.template.text)
                .replace('$item$', item);
          defered.resolve({
            template: template,
            callback: callback
          });
        }
      }

      /**
       * Get the ActionClasses for the Action
       *
       * This returns 'btn-danger' for the 'delete' and 'danger'
       * action types for row and 'btn-default' for other action
       * type for row.
       *
       * For batch types, the classes are determined as given in the template.
       *
       */
      function getActionClasses(action, index, numPermittedActions) {
        var actionClassesParam = action.template.actionClasses || "";
        if (listType === 'row') {
          if (numPermittedActions === 1 || index === 0) {
            var actionClasses = "btn ";
            if (action.template.type === "delete" || action.template.type === 'danger') {
              actionClasses += "btn-danger ";
            } else {
              actionClasses += "btn-default ";
            }
            return actionClasses + actionClassesParam;
          } else {
            if (action.template.type === "delete" || action.template.type === 'danger') {
              return 'text-danger' + actionClassesParam;
            } else {
              return actionClassesParam;
            }
          }
        } else {
          return actionClassesParam;
        }
      }

      /**
       * Gets the Template URL for the Action
       * The template can be
       * 1. Explicit URL
       * 2. Based of a list of known templates
       * 3. Based of the type of List
       *
       * Uses the `listType` which can either be `row` or `batch`.
       */
      function getTemplateUrl(action) {
        if (angular.isDefined(action.template.url)) {
          // use the given URL
          return action.template.url;
        } else if (angular.isDefined(action.template.type)) {
          // determine the template by the given type
          return basePath + 'action-list/actions-' + action.template.type + '.template.html';
        } else {
          // determine the template by `listType` which can be row or batch
          return basePath + 'action-list/actions-' + listType + '.template.html';
        }
      }

    }

  } // end of service
})(); // end of IIFE
