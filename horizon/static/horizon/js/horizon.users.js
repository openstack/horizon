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
    var msg = "<span id='" + error_id + "' class='help-block'>" + gettext("Passwords do not match.") + "</span>";

    var password = $("#id_password").val();
    var confirm_password = $("#id_confirm_password").val();

    if (password !== confirm_password && $("#" + error_id).length === 0) {
      $(row).parent().addClass("has-error").append(msg);
    } else if (password === confirm_password) {
      $(row).parent().removeClass("has-error");
      $("#" + error_id).remove();
    }
  }
};

