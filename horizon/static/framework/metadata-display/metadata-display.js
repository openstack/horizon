(function () {
  'use strict';

  /**
   * @ngdoc overview
   * @name hz.widget.metadata-display
   * @description
   *
   * # hz.widget.metadata-display
   *
   * The `hz.widget.metadata-display` provides widget displaying metadata.
   *
   * | Directives                                                                                  |
   * |---------------------------------------------------------------------------------------------|
   * | {@link hz.widget.metadata-display.directive:hzMetadataDisplay `hzMetadataDisplay`}          |
   * |---------------------------------------------------------------------------------------------|
   * | Controllers                                                                                 |
   * |---------------------------------------------------------------------------------------------|
   * | {@link hz.widget.metadata-display.controller:hzMetadataDisplayCtrl `hzMetadataDisplayCtrl`} |
   *
   */
  angular.module('hz.widget.metadata-display', [
    'hz.widget.metadata-tree'
  ])

  /**
   * @ngdoc parameters
   * @name hz.widget.metadata-display:metadataTreeDefaults
   * @param {object} text Text constants
   */
  .constant('metadataDisplayDefaults', {
    text: {
      detail: gettext('Detail Information')
    }
  })

  /**
   * @ngdoc directive
   * @name hz.widget.metadata-display.directive:hzMetadataDisplay
   * @scope
   *
   * @description
   * The `hzMetadataDisplay` displays existing metadata.
   *
   * @param {object[]} available List of available namespaces
   * @param {object} existing Key-value pairs with existing properties
   * @param {object=} text Text override
   */
  .directive('hzMetadataDisplay', ['basePath',
    function (path) {
      return {
        scope: {
          available: '=',
          existing: '=',
          text: '=?'
        },
        controller: 'hzMetadataDisplayCtrl',
        templateUrl: path + 'metadata-display/metadata-display.html'
      };
    }
  ])

  /**
   * @ngdoc controller
   * @name hz.widget.metadata-display.controller:hzMetadataDisplayCtrl
   * @description
   * Controller used by `hzMetadataDisplay`
   */
  .controller('hzMetadataDisplayCtrl', [
    '$scope', 'metadataTreeService', 'metadataDisplayDefaults',
    function ($scope, metadataTreeService, defaults) {

      function init() {
        $scope.tree = new metadataTreeService.Tree($scope.available, $scope.existing);
        angular.forEach($scope.tree.flatTree, function (item) {
          if(item.added) {
            if(!item.leaf) {
              item.added = false;
              if (item.parent) {
                item.parent.addedCount -= 1;
              }
            }
            else if(!item.custom) {
              $scope.hide = false;
            }
          }

        });
        // select first item
        $scope.tree.flatTree.some(function (item) {
          if($scope.listFilter(item)) {
            $scope.selected = item;
            item.expand(true);
            return true; // break
          }
        });
      }

      $scope.onSelect = function (item) {
        $scope.selected.collapse();
        item.expand(true);
        $scope.selected = item;
      };

      $scope.childrenFilter = function (item) {
        return item.visible && item.leaf && item.added;
      };

      $scope.listFilter = function (item) {
        return item.addedCount > 0;
      };

      $scope.text = angular.extend({}, defaults.text, $scope.text);
      $scope.tree = null;
      $scope.selected = null;
      $scope.hide = true;

      init();
    }
  ]);

}());
