/* Namespace for core functionality related to Forms. */
horizon.forms = {
  handle_source_group: function() {
    $(document).on("change", "#id_source_group", function (evt) {
      var $sourceGroup = $('#id_source_group'),
          $cidrContainer = $('#id_cidr').closest(".control-group");
      if($sourceGroup.val() === "") {
        $cidrContainer.removeClass("hide");
      } else {
        $cidrContainer.addClass("hide");
      }
    });
  }
};

horizon.forms.bind_add_item_handlers = function (el) {
  var $selects = $(el).find('select[data-add-item-url]');
  $selects.each(function () {
    var $this = $(this);
        $button = $("<a href='" + $this.attr("data-add-item-url") + "' " +
                    "data-add-to-field='" + $this.attr("id") + "' " +
                    "class='btn ajax-add ajax-modal'>+</a>");
    $this.after($button);
  });
};

horizon.forms.prevent_multiple_submission = function (el) {
  // Disable multiple submissions when launching a form.
  var $form = $(el).find("form");
  $form.submit(function () {
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
};

horizon.addInitFunction(function () {
  horizon.forms.prevent_multiple_submission($('body'));
  horizon.modals.addModalInitFunction(horizon.forms.prevent_multiple_submission);

  horizon.forms.bind_add_item_handlers($("body"));
  horizon.modals.addModalInitFunction(horizon.forms.bind_add_item_handlers);

  horizon.forms.handle_source_group();

  // Bind event handlers to confirm dangerous actions.
  $("body").on("click", "form button.btn-danger", function (evt) {
    horizon.datatables.confirm(this);
    evt.preventDefault();
  });

  /* Switchable fields */

  // Bind handler for swapping labels on "switchable" fields.
  $(document).on("change", 'select.switchable', function (evt) {
    var type = $(this).val();
    $(this).closest('fieldset').find('input[type=text]').each(function(index, obj){
      var label_val = "";
      if ($(obj).attr("data-" + type)){
        label_val = $(obj).attr("data-" + type);
      } else if ($(obj).attr("data")){
        label_val = $(obj).attr("data");
      } else
         return true;
      $('label[for=' + $(obj).attr('id') + ']').html(label_val);
    });
  });
  // Fire off the change event to trigger the proper initial values.
  $('select.switchable').trigger('change');
  // Queue up the even for use in new modals, too.
  horizon.modals.addModalInitFunction(function (modal) {
    $(modal).find('select.switchable').trigger('change');
  });


  /* Help tooltips */

  // Apply standard handler for everything but checkboxes.
  $(document).tooltip({
    selector: "div.form-field :input:not(:checkbox)",
    placement: function (tip, input) {
      // Position to the right unless this is a "split" for in which case put
      // the tooltip below so it doesn't block the next field.
      return $(input).closest("form[class*='split']").length ? "bottom" : 'right';
    },
    trigger: 'focus',
    title: function () {
      return $(this).closest('div.form-field').children('.help-block').text();
    }
  });
  // Hide the tooltip upon interaction with the field for select boxes.
  // We use mousedown and keydown since those "open" the select dropdown.
  $(document).on('mousedown keydown', '.form-field select', function (evt) {
    $(this).tooltip('hide');
  });
  // Hide the help text for js-capable browsers
  $('span.help-block').hide();


  /* Form examples */

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
