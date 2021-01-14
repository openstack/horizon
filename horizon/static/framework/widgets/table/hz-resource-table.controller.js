/*
 * (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP
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

  angular
    .module('horizon.framework.widgets.table')
    .controller('horizon.framework.widgets.table.ResourceTableController', controller);

  controller.$inject = [
    '$q',
    '$scope',
    'horizon.framework.widgets.table.events',
    'horizon.framework.widgets.magic-search.events',
    'horizon.framework.widgets.magic-search.service',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.app.core.openstack-service-api.settings'
  ];

  function controller(
    $q,
    $scope,
    hzTableEvents,
    magicSearchEvents,
    searchService,
    actionResultService,
    registry,
    settings
  ) {
    var ctrl = this;

    var lastSearchQuery = {};
    var timerRunning = false;

    // 'Public' Controller members
    ctrl.actionResultHandler = actionResultHandler;
    ctrl.searchFacets = [];
    ctrl.config = {};
    ctrl.batchActions = [];
    ctrl.items = [];
    ctrl.itemsSrc = [];
    ctrl.itemInTransitionFunction = itemInTransitionFunction;
    ctrl.ajaxPollInterval = 2500;
    settings.getSetting('AJAX_POLL_INTERVAL').then(
      function (response) {
        ctrl.ajaxPollInterval = response;
      });

    // Watch for changes to search bar
    $scope.$on(magicSearchEvents.SERVER_SEARCH_UPDATED, handleServerSearch);

    // Watch for changes to resourceTypeName
    $scope.$watch(
      "ctrl.resourceTypeName",
      onResourceTypeNameChange
    );

    // Watch for changes to listFunctionExtraParams
    $scope.$watch(
      "ctrl.listFunctionExtraParams",
      onListFunctionExtraParamsChange
    );

    // Local functions

    /**
     * Handle changes to resource type name
     *
     * @param newValue {string}
     * new resource type name
     */
    function onResourceTypeNameChange (newValue) {
      if (angular.isDefined(newValue)) {
        ctrl.resourceType = registry.getResourceType(newValue);
        ctrl.resourceType.initActions($scope);
        ctrl.searchFacets = ctrl.resourceType.filterFacets;
        ctrl.config = {
          detailsTemplateUrl: ctrl.resourceType.summaryTemplateUrl,
          selectAll: !!ctrl.resourceType.batchActions.length,
          expand: ctrl.resourceType.summaryTemplateUrl,
          trackId: ctrl.trackBy || 'id',
          columns: ctrl.resourceType.getTableColumns()
        };
        ctrl.batchActions = ctrl.resourceType.globalActions
          .concat(ctrl.resourceType.batchActions);
        checkForFilterFirstAndListResources();
      }
    }

    /**
     * Handle changes to list function extra params
     *
     * @param newValue {object}
     * new list function extra params
     */
    function onListFunctionExtraParamsChange (newValue) {
      if (angular.isDefined(newValue)) {
        checkForFilterFirstAndListResources();
      }
    }

    /**
     * First checks if the view needs a search criteria first before displaying
     * data
     *
     */
    function checkForFilterFirstAndListResources() {
      if (ctrl.resourceType) {
        ctrl.resourceType.needsFilterFirstFunction().then(resolve);
      }

      function resolve(result) {
        ctrl.config.needsFilterFirst = false;
        if (result) {
          if (checkForFiltersInSearchQuery()) {
            listResources();
          }
          else {
            ctrl.config.needsFilterFirst = true;
            ctrl.itemsSrc = [];
          }
        }
        else {
          listResources();
        }

      }

      function checkForFiltersInSearchQuery() {
        var filters = ctrl.searchFacets.filter(function (facet) {
          var queryParams = Object.keys(lastSearchQuery);
          return queryParams.indexOf(facet.name) > -1;
        });
        return filters.length > 0;
      }

    }

    /**
     * If a resource type has been set, list all resources for this resource type.
     * In the call to the list function, include the current search terms (if any)
     * and any extra list function params supplied by the parent (if any).
     */
    function listResources() {
      if (ctrl.resourceType) {
        ctrl.resourceType
          .list(angular.extend({}, lastSearchQuery, ctrl.listFunctionExtraParams))
          .then(onLoad);
      }
    }

    function handleServerSearch(evt, magicSearchQueryObj) {
      // Save the current search. We will use this if an action requires we re-list
      // resources, but still respect the current search terms.
      lastSearchQuery = searchService
        .getSearchTermsFromQueryString(magicSearchQueryObj.magicSearchQuery)
        .reduce(queryToObject, {});
      checkForFilterFirstAndListResources();

      function queryToObject(orig, curr) {
        var fields = searchService.getSearchTermObject(curr);
        orig[fields.type] = fields.value;
        return orig;
      }
    }

    function onLoad(response) {
      ctrl.itemsSrc = response.data.items;
      timerRunning = false;
    }

    function actionResultHandler(returnValue) {
      return $q.when(returnValue, actionSuccessHandler);
    }

    function actionSuccessHandler(result) { // eslint-disable-line no-unused-vars

      // The action has completed (for whatever "complete" means to that
      // action. Notice the view doesn't really need to know the semantics of the
      // particular action because the actions return data in a standard form.
      // That return includes the id and type of each created, updated, deleted
      // and failed item.
      //
      // This handler is also careful to check the type of each item. This
      // is important because actions which create non-items are launched from
      // the items page (like create "volume" from image).
      var deletedIds, updatedIds, createdIds, failedIds;

      if (result) {
        // Reduce the results to just item ids ignoring other types the action
        // may have produced
        deletedIds = actionResultService.getIdsOfType(result.deleted, ctrl.resourceType.type);
        updatedIds = actionResultService.getIdsOfType(result.updated, ctrl.resourceType.type);
        createdIds = actionResultService.getIdsOfType(result.created, ctrl.resourceType.type);
        failedIds = actionResultService.getIdsOfType(result.failed, ctrl.resourceType.type);

        // Handle deleted items
        if (deletedIds.length) {
          ctrl.itemsSrc = difference(ctrl.itemsSrc, deletedIds, 'id');
          $scope.$broadcast(hzTableEvents.CLEAR_SELECTIONS);
        }

        // Handle updated and created items
        if (updatedIds.length || createdIds.length) {
          // Ideally, get each created item individually, but
          // this is simple and robust for the common use case.
          // TODO: If we want more detailed updates, we could do so here.
          checkForFilterFirstAndListResources();
        }

        // Handle failed items
        if (failedIds.length) {
          // Do nothing for now.  Please note, actions may (and probably
          // should) provide toast messages when something goes wrong.
        }

      } else {
        // promise resolved, but no result returned. Because the action didn't
        // tell us what happened...reload the displayed items just in case.
        checkForFilterFirstAndListResources();
      }
    }

    function difference(currentList, otherList, key) {
      return currentList.filter(filter);

      function filter(elem) {
        return otherList.filter(function filterDeletedItem(deletedItem) {
          return deletedItem === elem[key];
        }).length === 0;
      }
    }

    function itemInTransitionFunction(item) {
      var itemInTransition = ctrl.resourceType.itemInTransitionFunction(item);
      if (ctrl.ajaxPollInterval && itemInTransition && !timerRunning) {
        timerRunning = true;
        setTimeout(listResources, ctrl.ajaxPollInterval);
      }
      return itemInTransition;
    }
  }

})();
