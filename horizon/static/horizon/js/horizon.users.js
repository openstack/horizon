horizon.user = {

  init: function() {
    $("#id_password").change(function () {
      if ($("#id_confirm_password").val() !== "") {
        horizon.user.check_passwords_match();
      }
    });

    $("#id_confirm_password").change(function () {
      horizon.user.check_passwords_match();
    });
  },

  check_passwords_match: function() {
    var row = $("input#id_confirm_password");
    var error_id = "id_confirm_password_error";
    var msg = "<span id='" + error_id + "' class='help-block alert alert-danger'>" + gettext("Passwords do not match.") + "</span>";

    var password = $("#id_password").val();
    var confirm_password = $("#id_confirm_password").val();

    if (password !== confirm_password && $("#" + error_id).length === 0) {
      $(row).parent().addClass("has-error");
      $(row).after(msg);
    } else if (password === confirm_password) {
      $(row).parent().removeClass("has-error");
      $("#" + error_id).remove();
    }
  }
};

