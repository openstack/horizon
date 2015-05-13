(function () {
  'use strict';

  /**
   * @ngdoc overview
   * @name hz.widget.metadata-tree
   * @description
   *
   * # hz.widget.metadata-tree
   *
   * The `hz.widget.metadata-tree` provides widgets and service
   * with logic for editing metadata.
   *
   * | Directives                                                                                 |
   * |--------------------------------------------------------------------------------------------|
   * | {@link hz.widget.metadata-tree.directive:hzMetadataTree `hzMetadataTree`}                  |
   * | {@link hz.widget.metadata-tree.directive:hzMetadataTreeItem `hzMetadataTreeItem`}          |
   * | {@link hz.widget.metadata-tree.directive:hzMetadataTreeUnique `hzMetadataTreeUnique`}      |
   * |--------------------------------------------------------------------------------------------|
   * | Controllers                                                                                |
   * |--------------------------------------------------------------------------------------------|
   * | {@link hz.widget.metadata-tree.controller:hzMetadataTreeCtrl `hzMetadataTreeCtrl`}         |
   * | {@link hz.widget.metadata-tree.controller:hzMetadataTreeItemCtrl `hzMetadataTreeItemCtrl`} |
   *
   */
  angular.module('hz.widget.metadata-tree', [])

  /**
   * @ngdoc parameters
   * @name hz.widget.metadata-tree.constant:metadataTreeDefaults
   * @param {object} text Text constants
   */
  .constant('metadataTreeDefaults', {
    text: {
      help: gettext('You can specify resource metadata by moving items from the left column to the right column. In the left columns there are metadata definitions from the Glance Metadata Catalog. Use the "Other" option to add metadata with the key of your choice.'),
      min: gettext('Min'),
      max: gettext('Max'),
      minLength: gettext('Min length'),
      maxLength: gettext('Max length'),
      patternMismatch: gettext('Pattern mismatch'),
      integerRequired: gettext('Integer required'),
      decimalRequired: gettext('Decimal required'),
      required: gettext('Required'),
      duplicate: gettext('Duplicate keys are not allowed'),
      filter: gettext('Filter'),
      available: gettext('Available Metadata'),
      existing: gettext('Existing Metadata'),
      custom: gettext('Custom'),
      noAvailable: gettext('No available metadata'),
      noExisting: gettext('No existing metadata')
    }
  })

  /**
   * @ngdoc directive
   * @name hz.widget.metadata-tree.directive:hzMetadataTree
   * @scope
   *
   * @description
   * The `hzMetadataTree` directive provide support for modifying existing
   * metadata properties and adding new from metadata catalog.
   *
   * @param {Tree=} model Model binding
   * @param {object[]=} available List of available namespaces
   * @param {object=} existing Key-value pairs with existing properties
   * @param {object=} text Text override
   */
  .directive('hzMetadataTree', ['basePath',
    function (path) {
      return {
        scope: {
          tree: '=*?model',
          available: '=?',
          existing: '=?',
          text: '=?'
        },
        controller: 'hzMetadataTreeCtrl',
        templateUrl: path + 'metadata-tree/metadata-tree.html'
      };
    }
  ])

  /**
   * @ngdoc directive
   * @name hz.widget.metadata-tree.directive:hzMetadataTreeItem
   * @scope
   *
   * @description
   * The `hzMetadataTreeItem` helper directive displays proper field for
   * editing Item.leaf.value depending on Item.leaf.type
   *
   * @param {expression} action Action for button
   * @param {Item} item Item to display
   * @param {object} text Text override
   */
  .directive('hzMetadataTreeItem', ['basePath',
    function (path) {
      return {
        scope: {
          action: '&',
          item: '=',
          text: '='
        },
        controller: 'hzMetadataTreeItemCtrl',
        templateUrl: path + 'metadata-tree/metadata-tree-item.html'
      };
    }
  ])

  /**
   * @ngdoc directive
   * @name hz.widget.metadata-tree.directive:hzMetadataTreeUnique
   * @restrict A
   *
   * @description
   * The `hzMetadataTreeUnique` helper directive provides validation
   * for field which value should be unique new Item
   */
  .directive('hzMetadataTreeUnique', function () {
    return {
      restrict: 'A',
      require: 'ngModel',
      link: function (scope, elm, attrs, ctrl) {
        ctrl.$validators.unique = function(modelValue, viewValue) {
          return !scope.tree.flatTree.some(function (item) {
            return item.leaf && item.leaf.name === viewValue;
          });
        };
      }
    };
  })

  /**
   * @ngdoc controller
   * @name hz.widget.metadata-tree.controller:hzMetadataTreeCtrl
   * @description
   * Controller used by `hzMetadataTree`
   */
  .controller('hzMetadataTreeCtrl', [
    '$scope', 'metadataTreeService', 'metadataTreeDefaults',
    function ($scope, metadataTreeService, defaults) {

      $scope.availableFilter = function (item) {
        return !item.added && (
            $scope.filterText.available.length === 0 ? item.visible : true);
      };

      $scope.text = angular.extend({}, defaults.text, $scope.text);
      if(!$scope.tree) {
        $scope.tree = new metadataTreeService.Tree($scope.available, $scope.existing);
      }
      $scope.customItem = '';
      $scope.filterText = {
        available: '',
        existing: ''
      };
    }
  ])

  /**
   * @ngdoc controller
   * @name hz.widget.metadata-tree.controller:hzMetadataTreeItemCtrl
   * @description
   * Controller used by `hzMetadataTreeItem`
   */
  .controller('hzMetadataTreeItemCtrl', [
    '$scope',
    function ($scope) {
      $scope.formatErrorMessage = function (item, error) {
        if(error.min) return $scope.text.min + ' ' + item.leaf.minimum;
        if(error.max) return $scope.text.max + ' ' + item.leaf.maximum;
        if(error.minlength) return $scope.text.minLength + ' ' + item.leaf.minLength;
        if(error.maxlength) return $scope.text.maxLength + ' ' + item.leaf.maxLength;
        if(error.pattern) {
          if(item.leaf.type === 'integer') return $scope.text.integerRequired;
          else return $scope.text.patternMismatch;
        }
        if(error.number) {
          if(item.leaf.type === 'integer') return $scope.text.integerRequired;
          else return $scope.text.decimalRequired;
        }
        if(error.required) {
          return $scope.text.required;
        }
      };

      function remove(array, value) {
        var index = array.indexOf(value);
        if (index > -1) {
          array.splice(index, 1);
        }
        return array;
      }

      $scope.opened = false;

      if($scope.item.leaf.type === 'array') {

        $scope.values = $scope.item.leaf.items.enum.filter(function(i) {
          return $scope.item.leaf.value.indexOf(i) < 0;
        }).sort();

        if(!$scope.item.leaf.readonly) {
          $scope.add = function (val) {
            $scope.item.leaf.value.push(val);
            $scope.item.leaf.value.sort();
            remove($scope.values, val);
          };

          $scope.remove = function (val) {
            remove($scope.item.leaf.value, val);
            $scope.values.push(val);
            $scope.values.sort();
            if ($scope.item.leaf.value.length === 0) {
              $scope.opened = true;
            }
          };

          $scope.open = function () {
            $scope.opened = !$scope.opened;
          };

          $scope.opened = $scope.item.leaf.value.length === 0;
        }
      }
    }
  ]);

}());
