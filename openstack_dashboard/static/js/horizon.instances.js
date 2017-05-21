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

/* global JSEncrypt */
horizon.instances = {
  user_volume_size: false,

  workflow_init: function () {
    // Initialise the drag and drop network list
    horizon.lists.generate_html("network");
  }
};

horizon.addInitFunction(horizon.instances.init = function () {
  var $document = $(document);

  $document.on('submit', '#tail_length', function (evt) {
    horizon.lists.get_console_log(true, true);
    evt.preventDefault();
  });

  /* Launch instance workflow */

  // Handle field toggles for the Launch Instance source type field
  function update_launch_source_displayed_fields (field) {
    var $this = $(field);
    var base_type = $this.val();
    var elements_list;

    $this.closest(".form-group").nextAll().hide();

    /*
     As part of fixing bug #1482507, Changing the image to default
     image for other than "Boot from image" source type, so that
     disableFlavorsForImages() is called on Image name change to reset flavors.
     */
    if (base_type != "image_id") {
      $("#id_image_id").val('');
      $('#id_image_id').change();
    }
    switch(base_type) {
      case "image_id":
        elements_list = "#id_image_id";
        break;
      case "instance_snapshot_id":
        elements_list = "#id_instance_snapshot_id";
        break;
      case "volume_id":
        elements_list = "#id_volume_id, #id_device_name, #id_vol_delete_on_instance_delete";
        break;
      case "volume_image_id":
        elements_list = "#id_image_id, #id_volume_size, #id_device_name, #id_vol_delete_on_instance_delete";
        break;
      case "volume_snapshot_id":
        elements_list = "#id_volume_snapshot_id, #id_device_name, #id_vol_delete_on_instance_delete";
        break;
    }
    var elements_list_group = $(elements_list).closest(".form-group");
    elements_list_group.addClass("required");
    // marking all the fields in 'elements_list' as mandatory except '#id_device_name'
    $("#id_device_name").closest(".form-group").removeClass("required");
    // showing all the fields in 'elements_list'
    elements_list_group.show();
  }

  $document.on('change', '.workflow #id_source_type', function () {
    update_launch_source_displayed_fields(this);
  });

  $('.workflow #id_source_type').change();
  horizon.modals.addModalInitFunction(function (modal) {
    $(modal).find("#id_source_type").change();
  });

  /*
   Update the device size value to reflect minimum allowed
   for selected image and flavor
   */
  function update_device_size(source_type) {
    var volume_size;
    var selected_flavor = horizon.Quota.getSelectedFlavor();
    if (selected_flavor) {
      volume_size = selected_flavor.disk;
    }
    var size_field = $("#id_volume_size");

    if (source_type === 'image') {
      var image = horizon.Quota.getSelectedImageOrSnapshot(source_type);
      if (image !== undefined && image.min_disk > volume_size) {
        volume_size = image.min_disk;
      }
      if (image !== undefined && image.size > volume_size) {
        volume_size = image.size;
      }
    }

    // If the user has manually changed the volume size, do not override
    // unless user-defined value is too small.
    if (horizon.instances.user_volume_size) {
      var user_value = size_field.val();
      if (user_value > volume_size) {
        volume_size = user_value;
      }
    }

    // Make sure the new value is >= the minimum allowed (1GB)
    if (volume_size < 1) {
      volume_size = 1;
    }

    size_field.val(volume_size);
  }

  $document.on('change', '.workflow #id_flavor', function () {
    update_device_size();
  });

  $document.on('change', '.workflow #id_image_id', function () {
    update_device_size('image');
  });

  $document.on('input', '.workflow #id_volume_size', function () {
    horizon.instances.user_volume_size = true;
    // We only need to listen for the first user input to this field,
    // so remove the listener after the first time it gets called.
    $document.off('input', '.workflow #id_volume_size');
  });

  horizon.instances.decrypt_password = function (encrypted_password, private_key) {
    var crypt = new JSEncrypt();
    crypt.setKey(private_key);
    return crypt.decrypt(encrypted_password);
  };

  $document.on('change', '#id_private_key_file', function (evt) {
    var file = evt.target.files[0];
    var reader = new FileReader();
    if (file) {
      reader.onloadend = function (event) {
        $("#id_private_key").val(event.target.result);
      };
      reader.onerror = function () {
        horizon.clearErrorMessages();
        horizon.toast.add('error', gettext('Could not read the file'));
      };
      reader.readAsText(file);
    }
    else {
      horizon.clearErrorMessages();
      horizon.toast.add('error', gettext('Could not decrypt the password'));
    }
  });
  /*
    The font-family is changed because with the default policy the major I
    and minor the l cannot be distinguished.
  */
  $document.on('show.bs.modal', '#password_instance_modal', function () {
    $("#id_decrypted_password").css({
      "font-family": "monospace",
      "cursor": "text"
    });
    $("#id_encrypted_password").css("cursor","text");
    $("#id_keypair_name").css("cursor","text");
  });

  $document.on('click', '#decryptpassword_button', function (evt) {
    var encrypted_password = $("#id_encrypted_password").val();
    var private_key = $('#id_private_key').val();
    if (!private_key) {
      evt.preventDefault();
      $(this).closest('.modal').modal('hide');
    }
    else {
      if (private_key.length > 0) {
        evt.preventDefault();
        var decrypted_password = horizon.instances.decrypt_password(encrypted_password, private_key);
        if (decrypted_password === false || decrypted_password === null) {
          horizon.clearErrorMessages();
          horizon.toast.add('error', gettext('Could not decrypt the password'));
        }
        else {
          $("#id_decrypted_password").val(decrypted_password);
          $("#decryptpassword_button").hide();
        }
      }
    }
  });
});
