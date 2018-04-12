/**
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

horizon.tabs = {
  _init_load_functions: []
};

horizon.tabs.addTabLoadFunction = function (f) {
  horizon.tabs._init_load_functions.push(f);
};

horizon.tabs.initTabLoad = function ($tab) {
  $tab.removeClass('tab-loading');
  $(horizon.tabs._init_load_functions).each(function (index, f) {
    f($tab);
  });
  recompileAngularContent($tab);
};

horizon.tabs.load_tab = function () {
  var $this = $(this),
    tab_id = $this.attr('data-target'),
    $tab_pane = $(tab_id);

  // Set up the client side template to append
  var $template = horizon.loader.inline(gettext('Loading'));

  $tab_pane
    .append($template)
    .addClass('tab-loading');

  // If query params exist, append tab id.
  if(window.location.search.length > 0) {
    $tab_pane.load(window.location.search + "&tab=" + tab_id.replace('#', ''), function() {
      horizon.tabs.initTabLoad($tab_pane);
    });
  } else {
    $tab_pane.load("?tab=" + tab_id.replace('#', ''), function() {
      horizon.tabs.initTabLoad($tab_pane);
    });
  }
  $this.attr("data-loaded", "true");
};

horizon.addInitFunction(horizon.tabs.init = function () {
  var data = horizon.cookies.getObject("tabs") || {};

  $(".tab-content").find(".js-tab-pane").addClass("tab-pane");
  horizon.modals.addModalInitFunction(function (el) {
    $(el).find(".js-tab-pane").addClass("tab-pane");
  });


  var $document = $(document);

  $document.on("show.bs.tab", ".ajax-tabs a[data-loaded='false']", horizon.tabs.load_tab);

  $document.on("shown.bs.tab", ".nav-tabs a[data-toggle='tab']", function (evt) {
    var $tab = $(evt.target),
      $content = $($(evt.target).attr('data-target'));
    $content.find("table.datatable").each(function () {
      horizon.datatables.update_footer_count($(this));
    });
    // d3 renders incorrectly in a hidden tab, this forces a rerender when the
    // container size is not 0 from display:none
    if($content.find(".d3-container").length) {
      window.dispatchEvent(new Event('resize'));
    }

    data[$tab.closest(".nav-tabs").attr("id")] = $tab.attr('data-target');
    horizon.cookies.putObject("tabs", data);
  });

  // Initialize stored tab state for tab groups on this page.
  $(".nav-tabs[data-sticky-tabs='sticky']").each(function () {
    var $this = $(this),
      id = $this.attr("id"),
      active_tab = data[id];
    // Set the tab from memory if we have a "sticky" tab and the tab wasn't explicitly requested via GET.
    if (active_tab && window.location.search.indexOf("tab=") < 0) {
      $this.find("a[data-target='" + active_tab + "']").tab('show');
    }
  });

  // Enable keyboard navigation between tabs in a form.
  $(".tab-content").on("keydown", ".tab-pane :input:visible:last", function (evt) {
    var $this = $(this),
      next_pane = $this.closest(".tab-pane").next(".tab-pane");
    // Capture the forward-tab keypress if we have a next tab to go to.
    if (evt.which === 9 && !evt.shiftKey && next_pane.length) {
      evt.preventDefault();
      $(".nav-tabs a[data-target='#" + next_pane.attr("id") + "']").tab('show');
    }
  });
  $(".tab-content").on("keydown", ".tab-pane :input:visible:first", function (evt) {
    var $this = $(this),
      prev_pane = $this.closest(".tab-pane").prev(".tab-pane");
    // Capture the forward-tab keypress if we have a next tab to go to.
    if (evt.shiftKey && evt.which === 9 && prev_pane.length) {
      evt.preventDefault();
      $(".nav-tabs a[data-target='#" + prev_pane.attr("id") + "']").tab('show');
      prev_pane.find(":input:last").focus();
    }
  });

  $document.on("focus", ".tab-content :input", function () {
    var $this = $(this),
      tab_pane = $this.closest(".tab-pane"),
      tab_id = tab_pane.attr('id');
    if (!tab_pane.hasClass("active")) {
      $(".nav-tabs a[data-target='#" + tab_id + "']").tab('show');
    }
  });
});

