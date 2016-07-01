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
    'horizon.framework.widgets.magic-search.events',
    'horizon.framework.widgets.magic-search.service',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.conf.resource-type-registry.service'
  ];

  function controller($q, $scope, events, searchService, actionResultService, registry) {
    var ctrl = this;

    // 'Public' Controller members

    ctrl.resourceType = registry.getResourceType(ctrl.resourceTypeName);
    ctrl.items = [];
    ctrl.itemsSrc = [];
    ctrl.searchFacets = ctrl.resourceType.filterFacets;
    ctrl.config = {
      detailsTemplateUrl: ctrl.resourceType.summaryTemplateUrl,
      selectAll: true,
      expand: true,
      trackId: ctrl.trackBy || 'id',
      columns: ctrl.resourceType.getTableColumns()
    };
    ctrl.batchActions = ctrl.resourceType.globalActions
      .concat(ctrl.resourceType.batchActions);

    ctrl.actionResultHandler = actionResultHandler;

    // Controller Initialization/Loading

    ctrl.resourceType.list().then(onLoad);
    ctrl.resourceType.initActions($scope);
    $scope.$on(events.SERVER_SEARCH_UPDATED, handleServerSearch);

    // Local functions

    function handleServerSearch(evt, magicSearchQueryObj) {
      var params = searchService
        .getSearchTermsFromQueryString(magicSearchQueryObj.magicSearchQuery)
        .reduce(queryToObject, {});
      ctrl.resourceType.list(params).then(onLoad);

      function queryToObject(orig, curr) {
        var fields = searchService.getSearchTermObject(curr);
        orig[fields.type] = fields.value;
        return orig;
      }
    }

    function onLoad(response) {
      ctrl.itemsSrc = response.data.items;
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

      if ( result ) {
        // Reduce the results to just item ids ignoring other types the action
        // may have produced
        deletedIds = actionResultService.getIdsOfType(result.deleted, ctrl.resourceType.type);
        updatedIds = actionResultService.getIdsOfType(result.updated, ctrl.resourceType.type);
        createdIds = actionResultService.getIdsOfType(result.created, ctrl.resourceType.type);
        failedIds = actionResultService.getIdsOfType(result.failed, ctrl.resourceType.type);

        // Handle deleted items
        if (deletedIds.length) {
          ctrl.itemsSrc = difference(ctrl.itemsSrc, deletedIds,'id');
        }

        // Handle updated and created items
        if ( updatedIds.length || createdIds.length ) {
          // Ideally, get each created item individually, but
          // this is simple and robust for the common use case.
          // TODO: If we want more detailed updates, we could do so here.
          ctrl.resourceType.list().then(onLoad);
        }

        // Handle failed items
        if (failedIds.length) {
          // Do nothing for now.  Please note, actions may (and probably
          // should) provide toast messages when something goes wrong.
        }

      } else {
        // promise resolved, but no result returned. Because the action didn't
        // tell us what happened...reload the displayed items just in case.
        ctrl.resourceType.list().then(onLoad);
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
  }

})();
