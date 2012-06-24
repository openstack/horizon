horizon.instances = {
  user_decided_length: false,

  getConsoleLog: function(via_user_submit) {
    var form_element = $("#tail_length"),
        data;

    if (!via_user_submit) {
      via_user_submit = false;
    }

    if(this.user_decided_length) {
      data = $(form_element).serialize();
    } else {
      data = "length=35";
    }

    $.ajax({
      url: $(form_element).attr('action'),
      data: data,
      method: 'get',
      success: function(response_body) {
        $('pre.logs').text(response_body);
      },
      error: function(response) {
        if(via_user_submit) {
          horizon.clearErrorMessages();
          horizon.alert('error', 'There was a problem communicating with the server, please try again.');
        }
      }
    });
  }
};

horizon.addInitFunction(function () {
  $(document).on('submit', '#tail_length', function (evt) {
    horizon.instances.user_decided_length = true;
    horizon.instances.getConsoleLog(true);
    evt.preventDefault();
  });
});
