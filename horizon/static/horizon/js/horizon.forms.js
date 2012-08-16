/* Namespace for core functionality related to Forms. */
horizon.forms = {
  handle_source_group: function() {
    $("div.table_wrapper, #modal_wrapper").on("change", "#id_source_group", function (evt) {
      var $sourceGroup = $('#id_source_group'),
          $cidrContainer = $('#id_cidr').closest(".control-group");
      if($sourceGroup.val() === "") {
        $cidrContainer.removeClass("hide");
      } else {
        $cidrContainer.addClass("hide");
      }
    });
  },
  handle_snapshot_source: function() {
    $("div.table_wrapper, #modal_wrapper").on("change", "select#id_snapshot_source", function(evt) {
      var $option = $(this).find("option:selected");
      var $form = $(this).closest('form');
      var $volName = $form.find('input#id_name');
      $volName.val($option.data("display_name"));
      var $volSize = $form.find('input#id_size');
      $volSize.val($option.data("size"));
    });
  }
};

horizon.forms.bind_add_item_handlers = function (el) {
  var $selects = $(el).find('select[data-add-item-url]');
  $selects.each(function () {
    var $this = $(this);
        $button = $("<a href='" + $this.attr("data-add-item-url") + "' " +
                    "data-add-to-field='" + $this.attr("id") + "' " +
                    "class='btn ajax-add ajax-modal btn-inline'>+</a>");
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

horizon.forms.init_examples = function (el) {
  var $el = $(el);

  // FIXME(gabriel): These should be moved into the forms themselves as help text, etc.
  // Generic examples.
  $el.find("#id_description").attr("placeholder", gettext("Additional information here..."));

  // Update/create image form.
  $el.find("#create_image_form input#id_copy_from").attr("placeholder", "http://example.com/image.iso");

  // Table search box.
  $el.find(".table_search input").attr("placeholder", gettext("Filter"));

  // Volume attachment form.
  $el.find("#attach_volume_form #id_device").attr("placeholder", "/dev/vdc/");
};

horizon.addInitFunction(function () {
  horizon.forms.prevent_multiple_submission($('body'));
  horizon.modals.addModalInitFunction(horizon.forms.prevent_multiple_submission);

  horizon.forms.bind_add_item_handlers($("body"));
  horizon.modals.addModalInitFunction(horizon.forms.bind_add_item_handlers);

  horizon.forms.init_examples($("body"));
  horizon.modals.addModalInitFunction(horizon.forms.init_examples);

  horizon.forms.handle_source_group();
  horizon.forms.handle_snapshot_source();

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
      if ($(obj).data(type)){
        label_val = $(obj).data(type);
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
});
