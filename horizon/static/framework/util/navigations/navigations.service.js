/*
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
    .module('horizon.framework.util.navigations')
    .factory('horizon.framework.util.navigations.service', navigationsService);

  function navigationsService() {

    return {
      getActivePanelUrl: getActivePanelUrl,
      collapseAllNavigation: collapseAllNavigation,
      expandNavigationByUrl: expandNavigationByUrl,
      setBreadcrumb: setBreadcrumb,
      isNavigationExists: isNavigationExists
    };

    /* get URL for active panel on navigation side bar */
    function getActivePanelUrl() {
      return angular.element('a.openstack-panel.active').attr('href');
    }

    /* collapse all nodes on navigation side bar */
    function collapseAllNavigation() {
      // collapse all dashboards
      var dashboards = angular.element(".openstack-dashboard").children("a");
      dashboards.addClass("collapsed").attr("aria-expanded", false);
      dashboards.siblings("ul").removeClass("in").attr("style", "height: 0px");

      // collapse all panelgroups
      var panelgroups = angular.element(".openstack-panel-group").children("a");
      panelgroups.addClass("collapsed").attr("aria-expanded", false);
      panelgroups.siblings("div").removeClass("in").attr("style", "height: 0px");

      // remove active from all panels
      angular.element("a.openstack-panel").removeClass("active");
    }

    /* expand specified node on navigation side bar */
    function expandNavigationByUrl(url) {
      // collapse all navigation
      collapseAllNavigation();

      var labels = [];

      // get panel on nav_bar
      var panel = angular.element("a.openstack-panel[href='" + url + "']");

      // get panelgroup on nav_bar
      var panelgroup = panel.parents(".openstack-panel-group").children("a");

      // get dashboard on nav_bar
      var dashboard = panel.parents(".openstack-dashboard").children("a");

      // open dashboard nav
      dashboard.removeClass("collapsed").attr("aria-expanded", true);
      dashboard.siblings("ul").addClass("in").attr("style", null);
      // get dashboard label
      labels.push(dashboard.text().trim());

      // open panelgroup on nav_bar if exists
      if (panelgroup.length) {
        panelgroup.removeClass("collapsed").attr("aria-expanded", true);
        // get panelgroup label
        labels.push(panelgroup.text().trim());
      }

      // open container for panels
      panel.parent().addClass("in").attr("style", null);

      // set panel active
      panel.addClass("active");
      // get panel label
      labels.push(panel.text().trim());

      return labels;
    }

    /* set breadcrumb items by array. The last item will be set as active */
    function setBreadcrumb(items) {
      var breadcrumb = angular.element("div.page-breadcrumb ol.breadcrumb");

      // remove all items
      breadcrumb.empty();

      // add items
      items.forEach(function (item, index, array) {
        var newItem = angular.element("<li>").addClass("breadcrumb-item-truncate");
        if (array.length - 1 === index) {
          newItem.addClass("active");
        }
        newItem.text(item);
        breadcrumb.append(newItem);
      });
    }

    /* check whether navigation exists from url */
    function isNavigationExists(url) {
      return angular.element("a.openstack-panel[href='" + url + "']").length ? true : false;
    }
  }
})();
