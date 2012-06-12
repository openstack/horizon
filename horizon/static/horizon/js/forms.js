horizon.addInitFunction(function () {
  // Disable multiple submissions when launching a form.
  $("form").submit(function () {
    $(this).submit(function () {
        return false;
    });
    $('input:submit').removeClass('primary').addClass('disabled');
    $('input:submit').attr('disabled', 'disabled');
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
