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
     * Wraps the JS code for displaying the theme preview page. Shouldn't be used elsewhere.
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

      //TODO(tqtran) Use angular, not jQuery
      $('a[href="#"]').click(function(e) {
        e.preventDefault();
      });

      var $uibModal = $('#source-modal');
      var $pre = $uibModal.find('pre');

      var $button = $('<div id="source-button" class="btn btn-primary btn-xs"><span class="fa fa-code"></span></div>')
        .click(function(){
          var $parent = $(this).parent();

          var $fragment = stripAngular($parent.clone());
          if ($parent.find('.line-chart').length) {
            // Use the stored fragment, since the line chart
            // init code changes the markup.
            $fragment = $line_chart_fragment;
          }

          // Remove Line chart svg elements
          $fragment = stripChart($fragment);
          var html = cleanSource($fragment.html());
          $pre.text(unescapeHtml(html));
          $uibModal.modal();
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
      horizon.forms.datepicker();
      $('#datepicker').datepicker();

      var line_chart_selector = '.line-chart';
      var line_chart_data = [
        {x: "2013-08-21T11:21:39", y: 1},
        {x: "2013-08-21T11:21:40", y: 4},
        {x: "2013-08-21T11:21:41", y: 6},
        {x: "2013-08-21T11:21:43", y: 8},
        {x: "2013-08-21T11:21:46", y: 10},
        {x: "2013-08-21T11:21:49", y: 11},
        {x: "2013-08-21T11:21:48", y: 10},
        {x: "2013-08-21T11:21:47", y: 8},
        {x: "2013-08-21T11:21:47", y: 7},
        {x: "2013-08-21T11:21:48", y: 5},
        {x: "2013-08-21T11:21:49", y: 4},
        {x: "2013-08-21T11:21:51", y: 3},
        {x: "2013-08-21T11:21:54", y: 3},
        {x: "2013-08-21T11:21:57", y: 4},
        {x: "2013-08-21T11:21:57", y: 12},
        {x: "2013-08-21T11:21:59", y: 9},
        {x: "2013-08-21T11:22:01", y: 9},
        {x: "2013-08-21T11:22:03", y: 12},
        {x: "2013-08-21T11:22:03", y: 4},
        {x: "2013-08-21T11:22:06", y: 3},
        {x: "2013-08-21T11:22:09", y: 3},
        {x: "2013-08-21T11:22:11", y: 4},
        {x: "2013-08-21T11:22:12", y: 5},
        {x: "2013-08-21T11:22:13", y: 7},
        {x: "2013-08-21T11:22:13", y: 8},
        {x: "2013-08-21T11:22:12", y: 10},
        {x: "2013-08-21T11:22:11", y: 11},
        {x: "2013-08-21T11:22:14", y: 10},
        {x: "2013-08-21T11:22:17", y: 8},
        {x: "2013-08-21T11:22:19", y: 6},
        {x: "2013-08-21T11:22:20", y: 4},
        {x: "2013-08-21T11:22:21", y: 1}
      ];

      $(line_chart_selector).data('data', {
        series: [
          {
            name: 'foo',
            data: line_chart_data
          }
        ],
        settings: {}
      });

      var $line_chart_fragment =
        $(line_chart_selector).attr('data-data', JSON.stringify(line_chart_data.slice(1,3))).parent().clone();

      horizon.d3_line_chart.init('.line-chart', {});
    }

  // Utility function to clean up the source code before displaying
  function stripAngular($frag) {
    $.each($frag.find('[translate]'), function(ndx, elem) {
      var $elem = $(elem);
      $elem
        .removeAttr('translate')
        .html($elem.find('> span').html());
    });
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

  function unescapeHtml(html) {
    return html.replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#039;/g, "'");
  }
})();
