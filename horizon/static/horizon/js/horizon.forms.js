/* Namespace for core functionality related to Forms. */
horizon.forms = {
  handle_snapshot_source: function() {
    $("div.table_wrapper, #modal_wrapper").on("change", "select#id_snapshot_source", function(evt) {
      var $option = $(this).find("option:selected");
      var $form = $(this).closest('form');
      var $volName = $form.find('input#id_name');
      if ($volName.val() == "") {
        $volName.val($option.data("name"));
      }
      var $volSize = $form.find('input#id_size');
      var volSize = parseInt($volSize.val(), 10) || -1;
      var dataSize = parseInt($option.data("size"), 10) || -1;
      if (volSize < dataSize) {
        $volSize.val(dataSize);
      }
    });
  },

  handle_volume_source: function() {
    $("div.table_wrapper, #modal_wrapper").on("change", "select#id_volume_source", function(evt) {
      var $option = $(this).find("option:selected");
      var $form = $(this).closest('form');
      var $volName = $form.find('input#id_name');
      if ($volName.val() == "") {
        $volName.val($option.data("name"));
      }
      var $volSize = $form.find('input#id_size');
      var volSize = parseInt($volSize.val(), 10) || -1;
      var dataSize = parseInt($option.data("size"), 10) || -1;
      if (volSize < dataSize) {
        $volSize.val(dataSize);
      }
    });
  },

  handle_image_source: function() {
    $("div.table_wrapper, #modal_wrapper").on("change", "select#id_image_source", function(evt) {
      var $option = $(this).find("option:selected");
      var $form = $(this).closest('form');
      var $volName = $form.find('input#id_name');
      if ($volName.val() == "") {
        $volName.val($option.data("name"));
      }
      var $volSize = $form.find('input#id_size');
      var volSize = parseInt($volSize.val(), 10) || -1;
      var dataSize = parseInt($option.data("size"), 10) || -1;
      var minDiskSize = parseInt($option.data("min_disk"), 10) || -1;
      var defaultVolSize = dataSize;
      if (minDiskSize > defaultVolSize) {
        defaultVolSize = minDiskSize;
      }
      if (volSize < defaultVolSize) {
        $volSize.val(defaultVolSize);
      }
    });
  },

  datepicker: function() {
    var startDate = $('input#id_start').datepicker()
      .on('changeDate', function(ev) {
        if (ev.date.valueOf() > endDate.date.valueOf()) {
          var newDate = new Date(ev.date);
          newDate.setDate(newDate.getDate() + 1);
          endDate.setValue(newDate);
          $('input#id_end')[0].focus();
        }
        startDate.hide();
      }).data('datepicker');

    var endDate = $('input#id_end').datepicker({
      onRender: function(date) {
        return date.valueOf() < startDate.date.valueOf() ? 'disabled' : '';
      }
    }).on('changeDate', function(ev) {
        endDate.hide();
      }).data('datepicker');
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

  // Update/create image form.
  $el.find("#create_image_form input#id_copy_from").attr("placeholder", "http://example.com/image.iso");

  // Table search box.
  $el.find(".table_search input").attr("placeholder", gettext("Filter"));

  // Volume attachment form.
  $el.find("#attach_volume_form #id_device").attr("placeholder", "/dev/vdc");
};

horizon.addInitFunction(function () {
  horizon.forms.prevent_multiple_submission($('body'));
  horizon.modals.addModalInitFunction(horizon.forms.prevent_multiple_submission);

  horizon.forms.bind_add_item_handlers($("body"));
  horizon.modals.addModalInitFunction(horizon.forms.bind_add_item_handlers);

  horizon.forms.init_examples($("body"));
  horizon.modals.addModalInitFunction(horizon.forms.init_examples);

  horizon.forms.handle_snapshot_source();
  horizon.forms.handle_volume_source();
  horizon.forms.handle_image_source();
  horizon.forms.datepicker();

  // Bind event handlers to confirm dangerous actions.
  $("body").on("click", "form button.btn-danger", function (evt) {
    horizon.datatables.confirm(this);
    evt.preventDefault();
  });

  /* Switchable Fields (See Horizon's Forms docs for more information) */

  // Bind handler for swapping labels on "switchable" fields.
  $(document).on("change", 'select.switchable', function (evt) {
    var $fieldset = $(evt.target).closest('fieldset'),
      $switchables = $fieldset.find('.switchable');

    $switchables.each(function (index, switchable) {
      var $switchable = $(switchable),
        slug = $switchable.data('slug'),
        visible = $switchable.is(':visible'),
        val = $switchable.val();

      $fieldset.find('.switched[data-switch-on*="' + slug + '"]').each(function(index, input){
        var $input = $(input),
          data = $input.data(slug + "-" + val);

        if (typeof data === "undefined" || !visible) {
          $input.closest('.form-field').hide();
        } else {
          $('label[for=' + $input.attr('id') + ']').html(data);
          $input.closest('.form-field').show();
        }
      });
    });
  });

  // Fire off the change event to trigger the proper initial values.
  $('select.switchable').trigger('change');
  // Queue up the for new modals, too.
  horizon.modals.addModalInitFunction(function (modal) {
    $(modal).find('select.switchable').trigger('change');
  });

  // Handle field toggles for the Create Volume source type field
  function update_volume_source_displayed_fields (field) {
    var $this = $(field),
      base_type = $this.val();

    $this.find("option").each(function () {
      if (this.value !== base_type) {
        $("#id_" + this.value).closest(".control-group").hide();
      } else {
        $("#id_" + this.value).closest(".control-group").show();
      }
    });
  }

  $(document).on('change', '#id_volume_source_type', function (evt) {
    update_volume_source_displayed_fields(this);
  });

  $('#id_volume_source_type').change();
  horizon.modals.addModalInitFunction(function (modal) {
    $(modal).find("#id_volume_source_type").change();
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
  // Hide the tooltip after escape button pressed
  $(document).on('keydown.esc_btn', function (evt) {
    if (evt.keyCode === 27) {
      $('.tooltip').hide();
    }
  });

  // Hide the help text for js-capable browsers
  $('span.help-block').hide();
});
