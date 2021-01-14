/*    Copyright (c) 2015 Mirantis, Inc.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

         http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.
*/

/*
 NOTE(tsufiev): the purpose of this code is to mark the titles of expanded
 dashboards and panel groups with special 'selenium-active' class that
 integration tests can use to understand what dashboard/panel group is
 currently open (and whether or not it needs to click it to proceed to some
 other dashboard/panel group). The need for this code arises from 2 facts:
  * since https://review.opendev.org/#/c/209259/ sidebar's expand/collapse
  behavior doesn't rely on JS code (pure CSS instead) - which is good;
  * to match dashboard/panel group header _before_ the 'li.panel-collapse.in'
  we need '!' selector which will be supported only in CSS4 (not going soon).
 */
horizon.selenium = {
  ACTIVE_CLS: 'selenium-active',
  ACTIVATION_DELAY: 1000
};

horizon.addInitFunction(horizon.selenium.init = function() {
  horizon.selenium.initSideBarHelpers();
  horizon.selenium.initDropdownHelpers();
});

horizon.selenium.initSideBarHelpers = function() {
  var $activeEntry = $('.openstack-dashboard-active > ul.panel-collapse.in');
  var dashboardLoc = '.openstack-dashboard';
  var groupLoc = 'li.openstack-panel-group';
  var activeCls = horizon.selenium.ACTIVE_CLS;

  var $activeDashboard = $activeEntry.closest(dashboardLoc).toggleClass(activeCls);
  var $activeGroup = $activeEntry.find(
    'li.openstack-panel-group > ul.panel-collapse.in'
  ).closest(groupLoc).toggleClass(activeCls);

  function toggleActiveDashboard($dashboard) {
    if ($activeDashboard) {
      $activeDashboard.toggleClass(activeCls);
    }
    if ($activeDashboard === $dashboard) {
      $activeDashboard = null;
    } else {
      $activeDashboard = $dashboard.toggleClass(activeCls);
      toggleActiveGroup($activeDashboard.find(groupLoc + ':eq(0)'));
    }
  }

  function toggleActiveGroup($group) {
    if ($group.length) {
      if ($activeGroup) {
        $activeGroup.toggleClass(activeCls);
      }
      if ($activeGroup === $group) {
        $activeGroup = null;
      } else {
        $activeGroup = $group.toggleClass(activeCls);
      }
    }
  }

  $(document).on('click', dashboardLoc, function() {
    toggleActiveDashboard($(this));
  }).on('click', groupLoc, function(event) {
    toggleActiveGroup($(this));
    // prevent the event from toggling an active dashboard
    event.stopPropagation();
  });
};

horizon.selenium.initDropdownHelpers = function() {
  var dropdownLoc = '.dropdown';
  window.setTimeout(function() {
    $(document).find(dropdownLoc).toggleClass(horizon.selenium.ACTIVE_CLS, true);
  }, horizon.selenium.ACTIVATION_DELAY);
};

