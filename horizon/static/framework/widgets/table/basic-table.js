(function() {
  'use strict';

  angular.module('horizon.framework.widgets.table')

    .constant('horizon.framework.widgets.table.filterPlaceholderText', gettext('Filter'))
    /**
     * @ngdoc directive
     * @name horizon.framework.widgets.table.directive:searchBar
     * @element
     * @param {string} {array} groupClasses Input group classes (optional)
     * @param {string} {array} iconClasses Icon classes (optional)
     * @param {string} {array} inputClasses Search field classes (optional)
     * @param {string} placeholder input field placeholder text (optional)
     * @description
     * The `searchBar` directive generates a search field that will
     * trigger filtering of the associated Smart-Table.
     *
     * groupClasses - classes that should be applied to input group element
     * iconClasses - classes that should be applied to search icon
     * inputClasses - classes that should be applied to search input field
     * placeholder - text that will be used for a placeholder attribute
     *
     * @restrict E
     *
     * @example
     * ```
     * <search-bar group-classes="input-group-sm"
     *   icon-classes="fa-search" input-classes="..." placeholder="Filter">
     * </search-bar>
     * ```
     */
    .directive('searchBar', ['horizon.framework.widgets.table.filterPlaceholderText',
      'horizon.framework.widgets.basePath',
      function(FILTER_PLACEHOLDER_TEXT, path) {
        return {
          restrict: 'E',
          templateUrl: path + 'table/search-bar.html',
          transclude: true,
          link: function (scope, element, attrs, ctrl, transclude) {
            if (angular.isDefined(attrs.groupClasses)) {
              element.find('.input-group').addClass(attrs.groupClasses);
            }
            if (angular.isDefined(attrs.iconClasses)) {
              element.find('.fa').addClass(attrs.iconClasses);
            }
            var searchInput = element.find('[st-search]');

            if (angular.isDefined(attrs.inputClasses)) {
              searchInput.addClass(attrs.inputClasses);
            }
            var placeholderText = attrs.placeholder || FILTER_PLACEHOLDER_TEXT;
            searchInput.attr('placeholder', placeholderText);

            transclude(scope, function(clone) {
              element.find('.input-group').append(clone);
            });
          }
        };
      }]);

}());
