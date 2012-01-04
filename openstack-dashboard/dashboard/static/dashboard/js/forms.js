horizon.addInitFunction(function() {
  // Disable multiple submissions when launching a form.
  $("form").submit(function() {
      $(this).submit(function() {
          return false;
      });
      $('input:submit').removeClass('primary').addClass('disabled');
      $('input:submit').attr('disabled', 'disabled');
      return true;
  });

  // TODO (tres): WTF?
  $(document).on("submit", ".modal #create_keypair_form", function(e) {
    var $this = $(this);
    $this.closest(".modal").modal("hide");
    $('#main_content .page-header').after('<div class="alert-message info">'
        + '<p><strong>Info: </strong>The data on this page may have changed, '
        + '<a href=".">click here to refresh it</a>.</p>'
        + '</div>');
    return true;
  });

  // Confirmation on deletion of items.
  // TODO (tres): These need to be localizable or to just plain go away in favor
  // of modals.
  $(".terminate").click(function() {
    var response = confirm('Are you sure you want to terminate the Instance: ' + $(this).attr('title') + "?");
    return response;
  });

  $(".delete").click(function(e) {
    var response = confirm('Are you sure you want to delete the ' + $(this).attr('title') + " ?");
    return response;
  });

  $(".reboot").click(function(e) {
    var response = confirm('Are you sure you want to reboot the ' + $(this).attr('title') + " ?");
    return response;
  });

  $(".disable").click(function(e) {
    var response = confirm('Are you sure you want to disable the ' + $(this).attr('title') + " ?");
    return response;
  });

  $(".enable").click(function(e) {
    var response = confirm('Are you sure you want to enable the ' + $(this).attr('title') + " ?");
    return response;
  });

  $(".detach").click(function(e) {
    var response = confirm('Are you sure you want to detach the ' + $(this).attr('title') + " ?");
    return response;
  });

  // Twipsy tooltips
  function getTwipsyTitle() {
      return $(this).closest('div.form-field').children('.help-block').text();
  }

  $("div.form-field").find("input:not(:checkbox), textarea, select").twipsy({
      placement:'right',
      trigger: 'focus',
      offset: 4,
      title: getTwipsyTitle
  });

  /* Trigger the twipsy on hover for checkboxes since focus only happens
     when the user clicks the element (which is too late for a tooltip to
     be useful). */
  $('div.form-field').has("input:checkbox").twipsy({
      placement: 'right',
      trigger: 'hover',
      offset: 4,
      title: getTwipsyTitle
  });

  // Hide the text for js-capable browsers
    $('span.help-block').hide();
});
