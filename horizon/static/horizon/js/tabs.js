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
  $(document).on("click", ".ajax-tabs a[data-loaded='false']", horizon.tabs.load_tab);
});
