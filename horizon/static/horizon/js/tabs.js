horizon.tabs = {};

horizon.tabs.load_tab = function (evt) {
  var $this = $(this),
      tab_id = $this.attr('data-target'),
      tab_pane = $(tab_id);
  tab_pane.append("<i class='icon icon-updating ajax-updating'></i>&nbsp;<span>loading...</span>");
  tab_pane.load("?tab=" + tab_id.replace('#', ''));
  $this.attr("data-loaded", "true");
  evt.preventDefault();
};

horizon.addInitFunction(function () {
  var data = horizon.cookies.read('tabs');

  $(document).on("show", ".ajax-tabs a[data-loaded='false']", horizon.tabs.load_tab);

  $(document).on("shown", ".nav-tabs a[data-toggle='tab']", function (evt) {
    var $tab = $(evt.target);
    horizon.cookies.update("tabs", $tab.closest(".nav-tabs").attr("id"), $tab.attr('data-target'));
  });

  // Initialize stored tab state for tab groups on this page.
  $(".nav-tabs[data-sticky-tabs='sticky']").each(function (index, item) {
    var $this = $(this),
        id = $this.attr("id"),
        active_tab = data[id];
    if (active_tab) {
      $this.find("a[data-target='" + active_tab + "']").tab('show');
    }
  });
});
