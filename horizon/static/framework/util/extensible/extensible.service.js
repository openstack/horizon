/*
 * Copyright 2015 IBM Corp.
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

  var $controller;

  angular
    .module('horizon.framework.util.extensible')
    .factory('horizon.framework.util.extensible.service', extensibleService);

  extensibleService.$inject = [
    '$controller'
  ];

  /**
   * @ngdoc service
   * @name horizon.framework.util.extensible.service:extensibleService
   * @module horizon.framework.util.extensible.service
   * @kind function
   * @description
   *
   * Make a container extensible by decorating it with functions that allow items to be added
   * or removed.
   *
   * @returns {Function} A function used to decorate a container to make it extensible.
   */
  function extensibleService(_$controller_) {
    $controller = _$controller_;
    return makeExtensible;
  }

  /**
   * A decorator function that makes the given container object extensible by allowing items to
   * be added or removed. This can be used on any object that contains multiple items where a user
   * might want to insert or remove their own items. Examples include workflow steps, table
   * actions, and form fields. Each item must have a unique ID within the container. It also adds
   * the ability to add controllers in the scope of the container. The following functions are
   * added to the container:
   *
   *   append(item, priority)
   *   prepend(item, priority)
   *   after(id, item, priority)
   *   remove(id)
   *   replace(id, item)
   *   addController(controller)
   *   initControllers($scope)
   *
   * Priorities are optional and determine the priority for multiple items placed at the same
   * position. Higher numbers mean lower priority. If not provided the item will have the lowest
   * priority (infinity).
   *
   * @param {Object} container - The container object to make extensible.
   * @param {Object} items - An array of all items in the container in display order. Each item
   *   should be an object and must have an id property that uniquely identifies the item within
   *   the container.
   *
   * For example, to make a workflow extensible:
   *
   *   extensibleService(workflow, workflow.steps);
   */
  function makeExtensible(container, items) {

    /**
     * Append a new item at the end of the container's items.
     *
     * @param {Object} item The item to append.
     * @param {Number} priority The optional priority for placement at the end of the container.
     * Lower priority (higher number) items will be placed at the end but before higher priority
     * (lower number) items.
     */
    container.append = function(item, priority) {
      if (!angular.isNumber(priority)) {
        priority = Infinity;
      }
      var itemsByPosition = getItemsByPosition(items, 'last').reverse();
      var index = items.length;
      for (var i = 0; i < itemsByPosition.length; i++) {
        if (priority > itemsByPosition[i]._ext.priority) {
          index = getItemIndex(items, itemsByPosition[i].id);
          break;
        }
      }
      item._ext = {position: 'last', priority: priority};
      items.splice(index, 0, item);
    };

    /**
     * Add a new item at the beginning of the container's items.
     *
     * @param {Object} item The item to add at the front.
     * @param {Number} priority The optional priority for placement at the front of the container.
     * Lower priority (higher number) items will be placed at the front but after higher priority
     * (lower number) items.
     */
    container.prepend = function(item, priority) {
      if (!angular.isNumber(priority)) {
        priority = Infinity;
      }
      var itemsByPosition = getItemsByPosition(items, 'first');
      var index = itemsByPosition.length;
      for (var i = 0; i < itemsByPosition.length; i++) {
        if (priority <= itemsByPosition[i]._ext.priority) {
          index = getItemIndex(items, itemsByPosition[i].id);
          break;
        }
      }
      item._ext = {position: 'first', priority: priority};
      items.splice(index, 0, item);
    };

    /**
     * Add a new item after the item with the given id.
     *
     * @param {String} id The id of an existing item in the container. The new item will be placed
     * after this item.
     * @param {Object} item The item to insert.
     * @param {Number} priority The optional priority for placement in the container at this
     * position. Higher priority (lower number) items will be placed more closely after the
     * given item id, followed by lower priority (higher number) items.
     */
    container.after = function(id, item, priority) {
      if (!angular.isNumber(priority)) {
        priority = Infinity;
      }
      var itemsByPosition = getItemsByPosition(items, 'after-' + id);
      var index = getItemIndex(items, id) + itemsByPosition.length + 1;
      for (var i = 0; i < itemsByPosition.length; i++) {
        if (priority <= itemsByPosition[i]._ext.priority) {
          index = getItemIndex(items, itemsByPosition[i].id);
          break;
        }
      }
      item._ext = {position: 'after-' + id, priority: priority};
      items.splice(index, 0, item);
    };

    /**
     * Remove an item from the container and return its index. When removing items from the
     * container you will need to account for any data the item might have been contributing to
     * the container's model. A custom controller could be used for this purpose and added using
     * the addController function.
     *
     * @param {String} id The id of the item to remove.
     *
     * @returns {Number} The index of the item being removed.
     */
    container.remove = function(id) {
      var index = getItemIndex(items, id);
      items.splice(index, 1);
      return index;
    };

    /**
     * Replace an item in the container with the one provided. The new item will need to account
     * for any data the original item might have been contributing to the container's model.
     *
     * @param {String} id The id of an existing item in the container. The item with this id will
     * be removed and the new item will be inserted in its place.
     * @param {Object} item The item to insert.
     */
    container.replace = function(id, item) {
      var index = container.remove(id);
      items.splice(index, 0, item);
    };

    /**
     * The controllers array keeps track of all controllers that should be instantiated with the
     * scope of the container.
     */
    container.controllers = [];

    /**
     * When an extensible container is instantiated, it should call this function to initialize
     * any additional controllers added by plugins. A typical plugin itself should not need to
     * call this, since any extensible containers created in horizon should be doing this.
     */
    container.initControllers = function($scope) {
      angular.forEach(container.controllers, function(ctrl) {
        $controller(ctrl, {$scope: $scope});
      });
    };

    /**
     * Add a custom controller to be instantiated with the scope of the container when a container
     * instance is created. This is useful in cases where a plugin removes an item or otherwise
     * wants to make changes to a container without adding any items. For example, to add some
     * custom validation to an existing item or react to certain container events.
     *
     * @param {String} ctrl The controller to add, e.g. 'MyFeatureController'.
     */
    container.addController = function(ctrl) {
      container.controllers.push(ctrl);
    };
  }

  /**
   * Get an array of items that have been added at a given position.
   *
   * @param {Array<Object>} items An array of all items in the container.
   * @param {String} position The position of the items to return. This can be "first",
   * "last", or "after-<id>".
   *
   * @returns {Array<Object>} An array of items. The returned items are sorted by priority. If
   * there are no items for the given position an empty array is returned. If two items have
   * the same priority then the last one added will "win". This is so the returned items are
   * always in the proper order for display purposes.
   */
  function getItemsByPosition(items, position) {
    return items.filter(function filterItems(item) {
      return item._ext && item._ext.position === position;
    }).sort(function sortItems(a, b) {
      return (a._ext.priority - b._ext.priority) || 1;
    });
  }

  /**
   * Get the index of a given item.
   *
   * @param {Array<Object>} items An array of all items in the container.
   * @param {String} id The id of an item. The index of the item will be returned.
   *
   * @returns {Number} The index of the item with the given id.
   */
  function getItemIndex(items, id) {
    for (var i = 0; i < items.length; i++) {
      if (items[i].id === id) {
        return i;
      }
    }
    throw new Error(interpolate('Item with id %(id)s not found.', {id: id}, true));
  }

})();
