(function() {
  'use strict';
  angular.module('MagicSearch', ['ui.bootstrap'])
    .directive('magicOverrides', function() {
      return {
        restrict: 'A',
        controller: ['$scope', '$timeout',
          function($scope, $timeout) {
            // showMenu and hideMenu depend on foundation's dropdown. They need
            // to be modified to work with another dropdown implemenation.
            // For bootstrap, they are not needed at all.
            $scope.showMenu = function() {
              $timeout(function() {
                $scope.isMenuOpen = true;
              });
            };
            $scope.hideMenu = function() {
              $timeout(function() {
                $scope.isMenuOpen = false;
              });
            };
            $scope.isMenuOpen = false;

            // magic_search.js should absorb this code?
            $scope.$on('facetsChanged', function() {
              $timeout(function() {
                $scope.currentSearch = [];
                $scope.initSearch();
              });
            });
          }
        ]
      }; // end of return
    }); // end of directive
})();