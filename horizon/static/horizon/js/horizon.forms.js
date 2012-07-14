/* Namespace for core functionality related to Forms. */
horizon.forms = {
  handle_source_group: function() {
    // Delegate this handler to form, so it only should be init once
    $("form").live("change", "#id_source_group", function(evt) {
      var $sourceGroup = $(this).find('#id_source_group');
      var $cidrContainer = $(this).find('#id_cidr').parent().parent();
      if($sourceGroup.val() === "") {
        $cidrContainer.removeClass("hide");
      } else {
        $cidrContainer.addClass("hide");
      }
    });
  }
};

horizon.addInitFunction(function () {
  // Disable multiple submissions when launching a form.
  $("form").submit(function () {
    var button = $(this).find('[type="submit"]');
    if (button.hasClass('btn-primary') && !button.hasClass('always-enabled')){
      $(this).submit(function () {
        return false;
      });
      button.removeClass('primary').addClass('disabled');
      button.attr('disabled', 'disabled');
    }
    return true;
  });

  horizon.datatables.validate_button();

  horizon.forms.handle_source_group();

  $('select.switchable').live("change", (function(e){
    var type = $(this).val();
    $(this).closest('fieldset').find('input[type=text]').each(function(index, obj){
      var label_val = "";
      if ($(obj).attr("data-"+type)){
        label_val = $(obj).attr("data-"+type);
      } else if ($(obj).attr("data")){
        label_val = $(obj).attr("data");
      } else
         return true;
      $('label[for='+ $(obj).attr('id') + ']').html(label_val);
      });
    }));
    $('select.switchable').trigger('change');
    $('body').on('shown', '.modal', function(evt) {
      $('select.switchable').trigger('change');
    });

  /* Twipsy tooltips */
  function getTwipsyTitle() {
    return $(this).closest('div.form-field').children('.help-block').text();
  }

  // Standard handler for everything but checkboxes
  $(document).tooltip({
    selector: "div.form-field input:not(:checkbox), div.form-field textarea, div.form-field select",
    placement: 'right',
    trigger: 'focus',
    title: getTwipsyTitle
  });
  $(document).on('change', '.form-field select', function (evt) {
    $(this).tooltip('hide');
  });

  // Hide the text for js-capable browsers
  $('span.help-block').hide();

  // Handle field toggles for the Launch Instance source type field
  function update_launch_source_displayed_fields (field) {
    var $this = $(field),
        base_type = $this.val();

    $this.find("option").each(function () {
      if (this.value != base_type) {
        $("#id_" + this.value).closest(".control-group").hide();
      } else {
        $("#id_" + this.value).closest(".control-group").show();
      }
    });
  }

  $(document).on('change', '.workflow #id_source_type', function (evt) {
    update_launch_source_displayed_fields(this);
  });

  $('.workflow #id_source_type').change();

  // Handle field toggles for the Launch Instance volume type field
  function update_launch_volume_displayed_fields (field) {
    var $this = $(field),
        volume_opt = $this.val(),
        $extra_fields = $("#id_delete_on_terminate, #id_device_name");

    $this.find("option").each(function () {
      if (this.value != volume_opt) {
        $("#id_" + this.value).closest(".control-group").hide();
      } else {
        $("#id_" + this.value).closest(".control-group").show();
      }
    });

    if (volume_opt === "volume_id" || volume_opt === "volume_snapshot_id") {
      $extra_fields.closest(".control-group").show();
    } else {
      $extra_fields.closest(".control-group").hide();
    }
  }
  $(document).on('change', '.workflow #id_volume_type', function (evt) {
    update_launch_volume_displayed_fields(this);
  });

  $('.workflow #id_volume_type').change();

});

horizon.addInitFunction(function() {
  // Update/create image form.
  $("#image_form input#id_name").example("ami-ubuntu");
  $("#image_form input#id_kernel").example("123");
  $("#image_form input#id_ramdisk").example("123");
  $("#image_form input#id_state").example("available");
  $("#image_form input#id_location").example("file:///var/lib/glance/images/123");
  $("#image_form input#id_architecture").example("x86_64");
  $("#image_form input#id_project_id").example("some");
  $("#image_form input#id_disk_format").example("ari");
  $("#image_form input#id_container_format").example("ari");
  $("#image_form input#id_ramdisk").example("123");

  // Launch instance form.
  $("#launch_img input#id_name").example("YetAnotherInstance");
  $("#launch_img input#id_security_groups").example("group1,group2");

  // Create flavor form.
  $("#flavor_form input#id_flavorid").example("1234");
  $("#flavor_form input#id_name").example("small");
  $("#flavor_form input#id_vcpus").example("256");
  $("#flavor_form input#id_memory_mb").example("256");
  $("#flavor_form input#id_disk_gb").example("256");

  // Update/create tenant.
  $("#tenant_form input#id__id").example("YetAnotherTenant");
  $("#tenant_form textarea#id_description").example("One or two sentence description.");

  // Update/create tenant.
  $("#user_form input#id_id").example("username");
  $("#user_form input#id_email").example("email@example.com");
  $("#user_form input#id_password").example("password");

  // Table search box.
  $(".table_search input").example("Filter");
});
