/*
 * (c) Copyright 2015 Hewlett Packard Enterprise Development Company LP
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

  angular
    .module('horizon.dashboard.developer.resource-browser')
    .controller('horizon.dashboard.developer.resource-browser.ResourceBrowserItemController',
      ResourceBrowserItemController);

  ResourceBrowserItemController.$inject = [
    '$scope',
    'horizon.dashboard.developer.resource-browser.BASE_ROUTE',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngdoc controller
   * @name horizon.dashboard.developer.resource-browser:ResourceBrowserItemController
   * @description
   * This controller allows the launching of any actions registered for resource types
   */
  function ResourceBrowserItemController($scope, baseRoute, toastService) {

    /**
     * Directive data (Private)
     */
    var ctrl = this;
    var typeData = ctrl.registryResourceType;
    var type = typeData.type;

    /**
     * View-specific model (Public)
     */
    ctrl.collapsed = true;
    ctrl.resourceId = undefined;
    ctrl.fullySupported = fullySupported();
    ctrl.typeLabel = type;
    ctrl.nameLabel = typeData.getName();
    ctrl.allNameLabels = [typeData.getName(1) || '', typeData.getName(2)];
    ctrl.supportsGenericTableView = supportsGenericTableView();
    ctrl.typeName = getName();
    ctrl.hasListFunction = hasListFunction();
    ctrl.listFunctionNameLabel = listFunctionNameLabel();
    ctrl.hasProperties = hasProperties();
    ctrl.hasTableColumns = hasTableColumns();
    ctrl.hasSummaryView = hasSummaryView();
    ctrl.summaryTemplateUrl = typeData.summaryTemplateUrl;
    ctrl.tableUrl = getTableUrl(type);
    ctrl.tableColumnLabels = getTableColumnLabels();
    ctrl.propertyLabels = getProperties();
    ctrl.supportsGenericDetailsView = supportsGenericDetailsView();
    ctrl.hasLoadFunction = hasLoadFunction();
    ctrl.loadFunctionNameLabel = loadFunctionNameLabel();
    ctrl.hasDetailView = hasDetailView();
    ctrl.detailViewLabels = getDetailViewLabels();
    ctrl.hasGlobalActions = hasGlobalActions();
    ctrl.globalActions = typeData.globalActions;
    ctrl.hasBatchActions = hasBatchActions();
    ctrl.batchActions = typeData.batchActions;
    ctrl.hasItemActions = hasItemActions();
    ctrl.itemActions = typeData.itemActions;

    /**
     * View-specific behavior (Public)
     */
    ctrl.onGlobalActionSelected = onGlobalActionSelected;
    ctrl.onActionSelected = onActionSelected;

    //////////////

    /**
     * Implementation
     */
    function fullySupported() {
      return supportsGenericDetailsView() &&
             supportsGenericTableView() &&
             hasSummaryView() &&
             hasGlobalActions() &&
             hasItemActions();
    }

    function getName() {
      return typeData.getName();
    }

    function supportsGenericTableView() {
      return getName() &&
             hasListFunction() &&
             hasProperties() &&
             hasTableColumns() &&
             hasSummaryView();
    }

    function hasListFunction() {
      return typeData.isListFunctionSet();
    }

    function listFunctionNameLabel() {
      var label = gettext("Not Set");
      if (hasListFunction()) {
        label = typeData.list.name;
      }
      return label;
    }

    function hasProperties() {
      return getProperties().length > 0;
    }

    function hasTableColumns() {
      return typeData.tableColumns.length > 0;
    }

    function getProperties() {
      var properties = typeData.getProperties();
      var keys = Object.keys(properties);
      return keys.map(getLabel);

      function getLabel(item) {
        return properties[item].label;
      }
    }

    function getTableColumnLabels() {
      return typeData.tableColumns.map(getColumnId);

      function getColumnId(item) {
        return item.id;
      }
    }

    function getTableUrl(type) {
      return baseRoute + type;
    }

    function supportsGenericDetailsView() {
      return hasDetailView() && hasLoadFunction();
    }

    function hasDetailView() {
      return typeData.detailsViews.length > 0;
    }

    function getDetailViewLabels() {
      return typeData.detailsViews.map(getName);

      function getName(item) {
        return item.name;
      }
    }

    function hasLoadFunction() {
      return typeData.isLoadFunctionSet();
    }

    function loadFunctionNameLabel() {
      var label = gettext("Not Set");
      if (hasLoadFunction()) {
        label = typeData.load.name;
      }
      return label;
    }

    function hasGlobalActions() {
      return typeData.globalActions.length !== 0;
    }

    function hasBatchActions() {
      return typeData.batchActions.length !== 0;
    }

    function hasItemActions() {
      return typeData.itemActions.length !== 0;
    }

    function hasSummaryView() {
      return typeData.summaryTemplateUrl;
    }

    function onGlobalActionSelected(action) {
      if (action.service.initAction) {
        action.service.initAction();
      }

      return action.service.perform(null, $scope.$new());
    }

    function onActionSelected(action) {
      // First, attempt to load the requested resource. Assume the user
      // typed in an ID object that is compatible with the load function.
      typeData.load(ctrl.resourceId).then(performAction, loadFailed);

      function performAction(resource) {
        if (action.service.initAction) {
          action.service.initAction();
        }

        return action.service.perform(resource.data, $scope.$new());
      }

      function loadFailed(reason) {
        var msg = interpolate(gettext("resource load failed: %s"), [reason]);
        toastService.add('error', msg);
      }
    }
  }

})();
