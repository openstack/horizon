(function() {
  'use strict';

  angular.module('hz.widget.table')

    /**
     * @ngdoc directive
     * @name hz.widget.table.directive:searchBar
     * @element
     * @param {string} {array} groupClasses Input group classes (optional)
     * @param {string} {array} iconClasses Icon classes (optional)
     * @param {string} {array} inputClasses Search field classes (optional)
     * @description
     * The `searchBar` directive generates a search field that will
     * trigger filtering of the associated Smart-Table.
     *
     * groupClasses - classes that should be applied to input group element
     * iconClasses - classes that should be applied to search icon
     * inputClasses - classes that should be applied to search input field
     *
     * @restrict E
     *
     * @example
     * ```
     * <search-bar group-classes="'input-group-sm'"
     *   icon-classes="'fa-search'" input-classes="...">
     * </search-bar>
     * ```
     */
    .directive('searchBar', [ 'basePath', function(path) {
      return {
        restrict: 'E',
        templateUrl: path + 'table/search-bar.html',
        link: function (scope, element, attrs) {
          if (angular.isDefined(attrs.groupClasses)) {
            element.find('.input-group').addClass(attrs.groupClasses);
          }
          if (angular.isDefined(attrs.iconClasses)) {
            element.find('.fa').addClass(attrs.iconClasses);
          }
          if (angular.isDefined(attrs.inputClasses)) {
            element.find('[st-search]').addClass(attrs.inputClasses);
          }
        }
      };
    }]);

}());