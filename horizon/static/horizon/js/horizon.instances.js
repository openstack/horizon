horizon.instances = {
  user_decided_length: false,
  user_volume_size: false,
  networks_selected: [],
  networks_available: [],

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
          horizon.alert('error', gettext('There was a problem communicating with the server, please try again.'));
        }
      }
    });
  },

  /*
   * Gets the html select element associated with a given
   * network id for network_id.
   **/
  get_network_element: function(network_id) {
    return $('li > label[for^="id_network_' + network_id + '"]');
  },

  /*
   * Initializes an associative array of lists of the current
   * networks.
   **/
  init_network_list: function () {
    horizon.instances.networks_selected = [];
    horizon.instances.networks_available = [];
    $(this.get_network_element("")).each(function () {
      var $this = $(this);
      var $input = $this.children("input");
      var name = horizon.escape_html($this.text().replace(/^\s+/, ""));
      var network_property = {
        "name": name,
        "id": $input.attr("id"),
        "value": $input.attr("value")
      };
      if ($input.is(":checked")) {
        horizon.instances.networks_selected.push(network_property);
      } else {
        horizon.instances.networks_available.push(network_property);
      }
    });
  },

  /*
   * Generates the HTML structure for a network that will be displayed
   * as a list item in the network list.
   **/
  generate_network_element: function(name, id, value) {
    var $li = $('<li>');
    $li.attr('name', value).html(name + '<em class="network_id">(' + value + ')</em><a href="#" class="btn btn-primary"></a>');
    return $li;
  },

  /*
   * Generates the HTML structure for the Network List.
   **/
  generate_networklist_html: function() {
    var self = this;
    var available_network = $("#available_network");
    var selected_network = $("#selected_network");
    var updateForm = function() {
      var networkListId = $("#networkListId");
      var lists = networkListId.find("li").attr('data-index',100);
      var active_networks = $("#selected_network > li").map(function(){
        return $(this).attr("name");
      });
      networkListId.find("input:checkbox").removeAttr('checked');
      active_networks.each(function(index, value){
        networkListId.find("input:checkbox[value=" + value + "]")
          .prop('checked', true)
          .parents("li").attr('data-index',index);
      });
      networkListId.find("ul").html(
        lists.sort(function(a,b){
          if( $(a).data("index") < $(b).data("index")) { return -1; }
          if( $(a).data("index") > $(b).data("index")) { return 1; }
          return 0;
        })
      );
    };
    $("#networkListSortContainer").show();
    $("#networkListIdContainer").hide();
    self.init_network_list();
    // Make sure we don't duplicate the networks in the list
    available_network.empty();
    $.each(self.networks_available, function(index, value){
      available_network.append(self.generate_network_element(value.name, value.id, value.value));
    });
    // Make sure we don't duplicate the networks in the list
    selected_network.empty();
    $.each(self.networks_selected, function(index, value){
      selected_network.append(self.generate_network_element(value.name, value.id, value.value));
    });
    // $(".networklist > li").click(function(){
    //   $(this).toggleClass("ui-selected");
    // });
    $(".networklist > li > a.btn").click(function(e){
      var $this = $(this);
      e.preventDefault();
      e.stopPropagation();
      if($this.parents("ul#available_network").length > 0) {
        $this.parent().appendTo(selected_network);
      } else if ($this.parents("ul#selected_network").length > 0) {
        $this.parent().appendTo(available_network);
      }
      updateForm();
    });
    if ($("#networkListId > div.form-group.error").length > 0) {
      var errortext = $("#networkListId > div.form-group.error span.help-block").text();
      $("#selected_network_label").before($('<div class="dynamic-error">').html(errortext));
    }
    $(".networklist").sortable({
      connectWith: "ul.networklist",
      placeholder: "ui-state-highlight",
      distance: 5,
      start:function(e,info){
        selected_network.addClass("dragging");
      },
      stop:function(e,info){
        selected_network.removeClass("dragging");
        updateForm();
      }
    }).disableSelection();
  },

  workflow_init: function(modal) {
    // Initialise the drag and drop network list
    horizon.instances.generate_networklist_html();
  }
};

horizon.addInitFunction(horizon.instances.init = function () {
  var $document = $(document);

  $document.on('submit', '#tail_length', function (evt) {
    horizon.instances.user_decided_length = true;
    horizon.instances.getConsoleLog(true);
    evt.preventDefault();
  });

  /* Launch instance workflow */

  // Handle field toggles for the Launch Instance source type field
  function update_launch_source_displayed_fields (field) {
    var $this = $(field);
    var base_type = $this.val();
    var elements_list;

    $this.closest(".form-group").nextAll().hide();

    switch(base_type) {
      case "image_id":
        elements_list = "#id_image_id";
        break;
      case "instance_snapshot_id":
        elements_list = "#id_instance_snapshot_id";
        break;
      case "volume_id":
        elements_list = "#id_volume_id, #id_device_name, #id_delete_on_terminate";
        break;
      case "volume_image_id":
        elements_list = "#id_image_id, #id_volume_size, #id_device_name, #id_delete_on_terminate";
        break;
      case "volume_snapshot_id":
        elements_list = "#id_volume_snapshot_id, #id_device_name, #id_delete_on_terminate";
        break;
    }
    var elements_list_group = $(elements_list).closest(".form-group");
    elements_list_group.addClass("required");
    // marking all the fields in 'elements_list' as mandatory except '#id_device_name'
    $("#id_device_name").closest(".form-group").removeClass("required");
    // showing all the fields in 'elements_list'
    elements_list_group.show();
  }

  $document.on('change', '.workflow #id_source_type', function (evt) {
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
  function update_device_size() {
    var volume_size = horizon.Quota.getSelectedFlavor().disk;
    var image = horizon.Quota.getSelectedImage();
    var size_field = $("#id_volume_size");

    if (image !== undefined && image.min_disk > volume_size) {
      volume_size = image.min_disk;
    }
    if (image !== undefined && image.size > volume_size) {
      volume_size = image.size;
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

  $document.on('change', '.workflow #id_flavor', function (evt) {
    update_device_size();
  });

  $document.on('change', '.workflow #id_image_id', function (evt) {
    update_device_size();
  });

  $document.on('input', '.workflow #id_volume_size', function (evt) {
    horizon.instances.user_volume_size = true;
    // We only need to listen for the first user input to this field,
    // so remove the listener after the first time it gets called.
    $document.off('input', '.workflow #id_volume_size');
  });

  horizon.instances.decrypt_password = function(encrypted_password, private_key) {
    var crypt = new JSEncrypt();
    crypt.setKey(private_key);
    return crypt.decrypt(encrypted_password);
  };

  $document.on('change', '#id_private_key_file', function (evt) {
    var file = evt.target.files[0];
    var reader = new FileReader();
    if (file) {
      reader.onloadend = function(event) {
        $("#id_private_key").val(event.target.result);
      };
      reader.onerror = function(event) {
        horizon.clearErrorMessages();
        horizon.alert('error', gettext('Could not read the file'));
      };
      reader.readAsText(file);
    }
    else {
      horizon.clearErrorMessages();
      horizon.alert('error', gettext('Could not decrypt the password'));
    }
  });
  /*
    The font-family is changed because with the default policy the major I
    and minor the l cannot be distinguished.
  */
  $document.on('show.bs.modal', '#password_instance_modal', function (evt) {
    $("#id_decrypted_password").css({
      "font-family": "monospace",
      "cursor": "text"
    });
    $("#id_encrypted_password").css("cursor","text");
    $("#id_keypair_name").css("cursor","text");
  });

  $document.on('click', '#decryptpassword_button', function (evt) {
    encrypted_password = $("#id_encrypted_password").val();
    private_key = $('#id_private_key').val();
    if (!private_key) {
      evt.preventDefault();
      $(this).closest('.modal').modal('hide');
    }
    else {
      if (private_key.length > 0) {
        evt.preventDefault();
        decrypted_password = horizon.instances.decrypt_password(encrypted_password, private_key);
        if (decrypted_password === false || decrypted_password === null) {
          horizon.clearErrorMessages();
          horizon.alert('error', gettext('Could not decrypt the password'));
        }
        else {
          $("#id_decrypted_password").val(decrypted_password);
          $("#decryptpassword_button").hide();
        }
      }
    }
  });
});
