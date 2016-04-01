/*
 *    (c) Copyright 2015 Cisco Systems, Inc.
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
    .module('horizon.dashboard.developer.theme-preview')
    .directive('themepreview', themePreview);

    themePreview.$inject = ['horizon.dashboard.developer.basePath'];

    /**
     * @ngdoc directive
     * @name themepreview
     * @description
     * Wraps the JS code for displaying the theme preview page. Shouldnt be used elsewhere.
     */

    function themePreview(path) {
      var directive = {
        restrict: 'E',
        templateUrl: path + 'theme-preview/theme-preview.html',
        link: link
      };

      return directive;
    }

    function link(scope, element) {

      //TODO(tqtran) Use angular, not jquery
      $('a[href="#"]').click(function(e) {
        e.preventDefault();
      });

      var $modal = $('#source-modal');
      var $pre = $modal.find('pre');

      var $button = $('<div id="source-button" class="btn btn-primary btn-xs"><span class="fa fa-code"></span></div>')
        .click(function(){
          var $fragment = stripAngular($(this).parent().clone());
          $fragment = stripChart($fragment);
          var html = cleanSource($fragment.html());
          $pre.text(html);
          $modal.modal();
      });

      var $component = $('.bs-component');
      $component.find('[data-toggle="popover"]').popover();
      $component.find('[data-toggle="tooltip"]').tooltip();

      $component.hover(function() {
        $(this).append($button);
        $button.show();
      });

      horizon.d3_pie_chart_distribution.init();
      horizon.d3_pie_chart_usage.init();
    }

  // Utility function to clean up the source code before displaying
  function stripAngular($frag) {
    var $translated = $frag.find('[translate]')
      .removeAttr('translate');
    $translated.html($translated.find('> span').html());
    $frag.find('.ng-scope').removeClass('ng-scope');
    $frag.find('.ng-pristine').removeClass('ng-pristine');
    $frag.find('.ng-valid').removeClass('ng-valid');
    $frag.find('input').removeAttr('style');
    return $frag;
  }

  // Utility function to clean up the source code before displaying
  function stripChart($frag) {
    $frag.find('.pie-chart-usage').find('svg').remove();
    $frag.find('.pie-chart-distribution').find('svg').remove();
    $frag.find('.pie-chart-distribution').find('.legend').remove();
    return $frag;
  }

  // Utility function to clean up the source code before displaying
  function cleanSource(html) {
      var lines = html.split(/\n/);
      lines.shift();
      lines.splice(-1, 1);
      var indentSize = lines[0].length - lines[0].trim().length;
      var re = new RegExp(' {' + indentSize + '}');
      lines = lines.map(function(line) {
        if (line.match(re)) {
          line = line.substring(indentSize);
        }
        return line;
      });
      lines = lines.join('\n');

      return lines;
    }
})();

