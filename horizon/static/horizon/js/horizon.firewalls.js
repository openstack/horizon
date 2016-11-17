horizon.firewalls = {
  workflow_init: function() {
    // Initialise the drag and drop rule list
    horizon.lists.generate_html("rule");
    horizon.lists.generate_html("router");
  }
};

horizon.addInitFunction(horizon.firewalls.init = function () {
  $(document).on('submit', '#tail_length', function (evt) {
    horizon.lists.get_console_log(true, true);
    evt.preventDefault();
  });
});
