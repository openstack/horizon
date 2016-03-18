horizon.tabs = {
  _init_load_functions: []
};

horizon.tabs.addTabLoadFunction = function (f) {
  horizon.tabs._init_load_functions.push(f);
};

horizon.tabs.initTabLoad = function (tab) {
  $(horizon.tabs._init_load_functions).each(function (index, f) {
    f(tab);
  });
  recompileAngularContent();
};

horizon.tabs.load_tab = function () {
  var $this = $(this),
    tab_id = $this.attr('data-target'),
    tab_pane = $(tab_id);

  // FIXME(gabriel): This style mucking shouldn't be in the javascript.
  tab_pane.append("<span style='margin-left: 30px;'>" + gettext("Loading") + "&hellip;</span>");
  tab_pane.spin(horizon.conf.spinner_options.inline);
  $(tab_pane.data().spinner.el).css('top', '9px');
  $(tab_pane.data().spinner.el).css('left', '15px');

  // If query params exist, append tab id.
  if(window.location.search.length > 0) {
    tab_pane.load(window.location.search + "&tab=" + tab_id.replace('#', ''), function() {
      horizon.tabs.initTabLoad(tab_pane);
    });
  } else {
    tab_pane.load("?tab=" + tab_id.replace('#', ''), function() {
      horizon.tabs.initTabLoad(tab_pane);
    });
  }
  $this.attr("data-loaded", "true");
};

horizon.addInitFunction(horizon.tabs.init = function () {
  var data = horizon.cookies.get("tabs") || {};

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
    data[$tab.closest(".nav-tabs").attr("id")] = $tab.attr('data-target');
    horizon.cookies.put("tabs", data);
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

horizon.tabs.addTabLoadFunction(horizon.inline_edit.init);
