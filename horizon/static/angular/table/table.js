/* jshint globalstrict: true */
(function() {
  'use strict';

  /**
   * @ngdoc overview
   * @name hz.widget.table
   * @description
   *
   * # hz.widget.table
   *
   * The `hz.widget.table` provides support for user interactions and checkbox
   * selection in tables.
   *
   * Requires {@link https://github.com/lorenzofox3/Smart-Table `Smart-Table`}
   * module and jQuery (for table drawer slide animation in IE9) to be installed.
   *
   * | Directives                                                        |
   * |-------------------------------------------------------------------|
   * | {@link hz.widget.table.directive:hzTable `hzTable`}               |
   * | {@link hz.widget.table.directive:hzSelectAll `hzSelectAll`}       |
   * | {@link hz.widget.table.directive:hzExpandDetail `hzExpandDetail`} |
   *
   */
  var app = angular.module('hz.widget.table', [ 'smart-table', 'lrDragNDrop' ]);

  /**
   * @ngdoc parameters
   * @name hz.widget.table.constant:expandSettings
   * @param {string} expandIconClasses Icon classes to be used for expand icon
   * @param {number} duration The slide down animation duration/speed
   */
  app.constant('expandSettings', {
    expandIconClasses: 'fa-chevron-right fa-chevron-down',
    duration: 400
  });

  /**
   * @ngdoc directive
   * @name hz.widget.table.directive:hzTable
   * @element table st-table='rowCollection'
   * @description
   * The `hzTable` directive extends the Smart-Table module to provide
   * support for saving the checkbox selection state of each row in the
   * table. Also included is the `updateSelectCount` function which
   * updates the checkbox selection count of the table. A default sort
   * key can be specified to sort the table initially by this key. To
   * reverse the sort, add default-sort-reverse='true' as well.
   *
   * @restrict A
   * @scope true
   * @example
   *
   * ```
   * <table st-table='rowCollection' hz-table default-sort="email">
   *  <thead>
   *    <tr>
   *      <th><input type='checkbox' hz-select-all='rowCollection'/></th>
   *      <th>Name</th>
   *    </tr>
   *  </thead>
   *  <tbody>
   *    <tr ng-repeat="row in rowCollection">
   *      <td>
   *        <input type='checkbox'
   *               ng-model='selected[row.id].checked'
   *               ng-change='updateSelectCount(row)'/>
   *      </td>
   *      <td>Foo</td>
   *    </tr>
   *  </tbody>
   * </table>
   * ```
   *
   */
  app.directive('hzTable', function() {
    return {
      restrict: 'A',
      require: 'stTable',
      scope: true,
      controller: function($scope) {
        $scope.selected = {};
        $scope.numSelected = 0;

        $scope.updateSelectCount = function(row) {
          if ($scope.selected.hasOwnProperty(row.id)) {
            var checkedState = $scope.selected[row.id].checked;

            if (checkedState) {
              $scope.numSelected += 1;
            } else {
              $scope.numSelected -= 1;
            }
          }
        };

        this.select = function(row, checkedState) {
          var oldCheckedState = $scope.selected.hasOwnProperty(row.id) ?
                                $scope.selected[row.id].checked :
                                false;

          $scope.selected[row.id] = {
            checked: checkedState,
            item: row
          };

          if (checkedState && !oldCheckedState) {
            $scope.numSelected += 1;
          } else if (!checkedState && oldCheckedState) {
            $scope.numSelected -= 1;
          }
        };
      },
      link: function(scope, element, attrs, stTableCtrl) {
        if (attrs.defaultSort) {
          var reverse = attrs.defaultSortReverse === 'true';
          stTableCtrl.sortBy(attrs.defaultSort, reverse);
        }
      }
    };
  });

  /**
   * @ngdoc directive
   * @name hz.widget.table.directive:hzSelectAll
   * @element input type='checkbox'
   * @description
   * The `hzSelectAll` directive updates the checkbox selection state of
   * every row in the table. Assign this as an attribute to a checkbox
   * input element, passing in the row collection data.
   *
   * @restrict A
   * @scope rows: '=hzSelectAll'
   * @example
   *
   * ```
   * <input type='checkbox' hz-select-all='rowCollection'/>
   * ```
   *
   */
  app.directive('hzSelectAll', function() {
    return {
      restrict: 'A',
      require: '^hzTable',
      scope: {
        rows: '=hzSelectAll'
      },
      link: function(scope, element, attrs, hzTableCtrl) {
        element.on('click', function() {
          scope.$apply(function() {
            var checkedState = element.prop('checked');
            angular.forEach(scope.rows, function(row) {
              hzTableCtrl.select(row, checkedState);
            });
          });
        });
      }
    };
  });

  /**
   * @ngdoc directive
   * @name hz.widget.table.directive:hzExpandDetail
   * @element i class='fa fa-chevron-right'
   * @param {number} duration The duration for drawer slide animation
   * @description
   * The `hzExpandDetail` directive toggles the detailed drawer of the row.
   * The animation is implemented using jQuery's slideDown() and slideUp().
   * Assign this as an attribute to an icon that should trigger the toggle,
   * passing in the two class names of the icon. If no class names are
   * specified, the default 'fa-chevron-right fa-chevron-down' is used. A
   * duration for the slide animation can be specified as well (default: 400).
   * The detail drawer row and cell also needs to be implemented and include
   * the classes 'detail-row' and 'detail', respectively.
   *
   * @restrict A
   * @scope icons: '@hzExpandDetail', duration: '@'
   * @example
   *
   * ```
   * <tr>
   *  <td>
   *    <i class='fa fa-chevron-right'
   *       hz-expand-detail='fa-chevron-right fa-chevron-down'
   *       duration='200'></i>
   *  </td>
   * </tr>
   * <tr class='detail-row'>
   *  <td class='detail'></td>
   * </tr>
   * ```
   *
   */
  app.directive('hzExpandDetail', [ 'expandSettings', function(settings) {
    return {
      restrict: 'A',
      scope: {
        icons: '@hzExpandDetail',
        duration: '@'
      },
      link: function(scope, element) {
        element.on('click', function() {
          var iconClasses = scope.icons || settings.expandIconClasses;
          element.toggleClass(iconClasses);

          var summaryRow = element.closest('tr');
          var detailCell = summaryRow.next('tr').find('.detail');
          var duration = scope.duration ? parseInt(scope.duration) : settings.duration;

          if (summaryRow.hasClass('expanded')) {
            var options = {
              duration: duration,
              complete: function() {
                // Hide the row after the slide animation finishes
                summaryRow.toggleClass('expanded');
              }
            };

            detailCell.find('.detail-expanded').slideUp(options);
          } else {
            summaryRow.toggleClass('expanded');

            if (detailCell.find('.detail-expanded').length === 0) {
              // Slide down animation doesn't work on table cells
              // so a <div> wrapper needs to be added
              detailCell.wrapInner('<div class="detail-expanded"></div>');
            }

            detailCell.find('.detail-expanded').slideDown(duration);
          }
        });
      }
    };
  }]);

})();