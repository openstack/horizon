horizon.alert = function (type, message, extra_tags) {
  var safe = false;
  // Check if the message is tagged as safe.
  if (typeof(extra_tags) !== "undefined" && $.inArray('safe', extra_tags.split(' ')) !== -1) {
    safe = true;
  }

  var type_display = {
    'danger': gettext("Danger: "),
    'warning': gettext("Warning: "),
    'info': gettext("Notice: "),
    'success': gettext("Success: "),
    'error': gettext("Error: ")
  }[type];

  // the "error" type needs to be rewritten as "danger" for correct styling
  if (type === 'error') {
    type = 'danger';
  }

  var template = horizon.templates.compiled_templates["#alert_message_template"],
    params = {
      "type": type || 'default',
      "type_display": type_display,
      "message": message,
      "safe": safe
    };
  var this_alert = $(template.render(params)).hide().prependTo("#main_content .messages").fadeIn(100);
  horizon.autoDismissAlert(this_alert);
  return this_alert;
};

horizon.clearErrorMessages = function() {
  $('#main_content .messages .alert.alert-danger').remove();
};

horizon.clearSuccessMessages = function() {
  $('#main_content .messages .alert.alert-success').remove();
};

horizon.clearAllMessages = function() {
  horizon.clearErrorMessages();
  horizon.clearSuccessMessages();
};

horizon.autoDismissAlert = function ($alert) {
  // If autofade isn't configured, don't do anything
  if (typeof(horizon.conf.auto_fade_alerts) === "undefined")
      return;

  var types = $alert.attr('class').split(' '),
    intersection = $.grep(types, function (value) {
      return $.inArray(value, horizon.conf.auto_fade_alerts.types) !== -1;
    });
  // Check if alert should auto-fade
  if (intersection.length > 0) {
    setTimeout(function() {
      $alert.fadeOut(horizon.conf.auto_fade_alerts.fade_duration);
    }, horizon.conf.auto_fade_alerts.delay);
  }
};

horizon.addInitFunction(function () {
  // Bind AJAX message handling.
  $(document).ajaxComplete(function(event, request){
    var message_array = $.parseJSON(horizon.ajax.get_messages(request));
    $(message_array).each(function (index, item) {
      horizon.alert(item[0], item[1], item[2]);
    });
  });

  // Dismiss alert messages when moving on to a new type of action.
  $('a.ajax-modal').click(function() {
    horizon.clearAllMessages();
  });

  // Bind dismiss(x) handlers for alert messages.
  $(".alert").alert();

  $('#main_content .messages .alert').each(function() {
    horizon.autoDismissAlert($(this));
  });
});
