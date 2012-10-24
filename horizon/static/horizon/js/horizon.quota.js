/*
  Used for animating and displaying quota information on forms which use the
  Bootstrap progress bars. Also used for displaying flavor details on modal-
  dialogs.

  Usage:
    In order to have progress bars that work with this, you need to have a
    DOM structure like this in your Django template:

    <div id="your_progress_bar_id" class="quota_bar">
      {% horizon_progress_bar total_number_used max_number_allowed %}
    </div>

    With this progress bar, you then need to add some data- HTML attributes
    to the div #your_progress_bar_id. The available data- attributes are:

      data-quota-used="integer" REQUIRED
          Integer representing the total number used by the user.

      data-quota-limit="integer" REQUIRED
          Integer representing the total quota limit the user has. Note this IS
          NOT the amount remaining they can use, but the total original quota.

      ONE OF THE THREE ATTRIBUTES BELOW IS REQUIRED:

      data-progress-indicator-step-by="integer" OPTIONAL
          Indicates the numeric unit the quota JavaScript should automatically
          animate this progress bar by on load. Can be used with the other
          data- attributes.

          A good use-case here is when you have a modal dialog to create ONE
          volume, and you have a progress bar for volumes, but there are no
          form elements that represent that number (as it is not settable by
          the user.)

      data-progress-indicator-for="html_id_of_form_input"
          Tells the quota JavaScript which form element on this page is tied to
          this progress indicator. If this form element is an input, it will
          automatically fire on "keyup" in that form field, and change this
          progress bar to denote the numeric change.

      data-progress-indicator-flavor
          This attribute is used to tell this quota JavaScript that this
          progress bar is controller by an instance flavor select form element.
          This attribute takes no value, but is used and configured
          automatically by this script to update when a new flavor is choosen
          by the end-user.
 */
horizon.Quota = {
  is_flavor_quota: false, // Is this a flavor-based quota display?
  user_value_progress_bars: [], // Progress bars triggered by user-changeable form elements.
  auto_value_progress_bars: [], // Progress bars that should be automatically changed.
  flavor_progress_bars: [], // Progress bars that relate to flavor details.
  user_value_form_inputs: [], // The actual form inputs that trigger progress changes.
  selected_flavor: null, // The flavor object of the current selected flavor on the form.
  flavors: [], // The flavor objects the form represents, passed to us in initWithFlavors.

  /*
    Determines the progress bars and form elements to be used for quota
    display. Also attaches handlers to the form elements as well as performing
    the animations when the progress bars first load.
  */
  init: function() {
    this.user_value_progress_bars = $('div[data-progress-indicator-for]');
    this.auto_value_progress_bars = $('div[data-progress-indicator-step-by]');
    this.user_value_form_inputs = $($.map(this.user_value_progress_bars, function(elm) {
      return ('#' + $(elm).attr('data-progress-indicator-for'));
    }));

    this._initialAnimations();
    this._attachInputHandlers();
  },

  /*
    Sets up the quota to be used with flavor form selectors, which requires
    some different handling of the forms. Also calls init() so that all of the
    other animations and handlers are taken care of as well when initializing
    with this method.
  */
  initWithFlavors: function(flavors) {
    this.is_flavor_quota = true;
    this.flavor_progress_bars = $('div[data-progress-indicator-flavor]');
    this.flavors = flavors;

    this.init();

    this.showFlavorDetails();
    this.updateFlavorUsage();
  },

  // Returns the flavor object for the selected flavor in the form.
  getSelectedFlavor: function() {
    if(this.is_flavor_quota) {
      this.selected_flavor = _.find(this.flavors, function(flavor) {
        return flavor.id == $("#id_flavor").children(":selected").val();
      });
    } else {
      this.selected_flavor = null;
    }

    return this.selected_flavor;
  },

  /*
    Populates the flavor details table with the flavor attributes of the
    selected flavor on the form select element.
  */
  showFlavorDetails: function() {
    this.getSelectedFlavor();

    if (this.selected_flavor) {
      var name = horizon.utils.truncate(this.selected_flavor.name, 14, true);
      var vcpus = horizon.utils.humanizeNumbers(this.selected_flavor.vcpus);
      var disk = horizon.utils.humanizeNumbers(this.selected_flavor.disk);
      var ephemeral = horizon.utils.humanizeNumbers(this.selected_flavor["OS-FLV-EXT-DATA:ephemeral"]);
      var disk_total = this.selected_flavor.disk + this.selected_flavor["OS-FLV-EXT-DATA:ephemeral"];
      var disk_total_display = horizon.utils.humanizeNumbers(disk_total);
      var ram = horizon.utils.humanizeNumbers(this.selected_flavor.ram);

      $("#flavor_name").html(name);
      $("#flavor_vcpus").text(vcpus);
      $("#flavor_disk").text(disk);
      $("#flavor_ephemeral").text(ephemeral);
      $("#flavor_disk_total").text(disk_total_display);
      $("#flavor_ram").text(ram);
    }
  },

  // Updates a progress bar, taking care of exceeding quota display as well.
  update: function(element, percentage_used, percentage_to_update) {
    var update_width = percentage_to_update;

    if(percentage_to_update + percentage_used > 100) {
      update_width = 100 - percentage_used;

      if(!element.hasClass('progress_bar_over')) {
        element.addClass('progress_bar_over');
      }
    } else {
      element.removeClass('progress_bar_over');
    }

    element.animate({width: parseInt(update_width, 10) + "%"}, 300);
  },

  /*
    When a new flavor is selected, this takes care of updating the relevant
    progress bars associated with the flavor quota usage.
  */
  updateFlavorUsage: function() {
    if(!this.is_flavor_quota) return;

    var scope = this;
    var instance_count = (parseInt($("#id_count").val(), 10) || 1);
    var update_amount = 0;

    this.getSelectedFlavor();

    $(this.flavor_progress_bars).each(function(index, element) {
      var element_id = $(element).attr('id');
      var progress_stat = element_id.match(/^quota_(.+)/)[1];

      if(progress_stat === undefined) {
        return;
      } else if(progress_stat === 'instances') {
        update_amount = instance_count;
      } else if (scope.selected_flavor) {
        update_amount = (scope.selected_flavor[progress_stat] * instance_count);
      }

      scope.updateUsageFor(element, update_amount);
    });
  },

  // Does the math to calculate what percentage to update a progress bar by.
  updateUsageFor: function(progress_element, increment_by) {
    progress_element = $(progress_element);

    var update_indicator = progress_element.find('.progress_bar_selected');
    var quota_limit = parseInt(progress_element.attr('data-quota-limit'), 10);
    var quota_used = parseInt(progress_element.attr('data-quota-used'), 10);
    var percentage_to_update = ((increment_by / quota_limit) * 100);
    var percentage_used = ((quota_used / quota_limit) * 100);

    this.update(update_indicator, percentage_used, percentage_to_update);
  },

  /*
    Attaches event handlers for the form elements associated with the
    progress bars.
  */
  _attachInputHandlers: function() {
    var scope = this;

    if(this.is_flavor_quota) {
      var eventCallback = function(evt) {
        scope.showFlavorDetails();
        scope.updateFlavorUsage();
      };

      $('#id_flavor').on('change', eventCallback);
      $('#id_count').on('keyup', eventCallback);
    }

    $(this.user_value_form_inputs).each(function(index, element) {
      $(element).on('keyup', function(evt) {
        var progress_element = $('div[data-progress-indicator-for=' + $(evt.target).attr('id') + ']');
        var integers_in_input = $(evt.target).val().match(/\d+/g);
        var user_integer;

        if(integers_in_input === null) {
          user_integer = 0;
        } else if(integers_in_input.length > 1) {
          /*
            Join all the numbers together that have been typed in. This takes
            care of junk input like "dd8d72n3k" and uses just the digits in
            that input, resulting in "8723".
          */
          user_integer = integers_in_input.join('');
        } else if(integers_in_input.length == 1) {
          user_integer = integers_in_input[0];
        }

        var progress_amount = parseInt(user_integer, 10);

        scope.updateUsageFor(progress_element, progress_amount);
      });
    });
  },

  /*
    Animate the progress bars of elements which indicate they should
    automatically be incremented, as opposed to elements which trigger
    progress updates based on form element input or changes.
  */
  _initialAnimations: function() {
    var scope = this;

    $(this.auto_value_progress_bars).each(function(index, element) {
      var auto_progress = $(element);
      var update_amount = parseInt(auto_progress.attr('data-progress-indicator-step-by'), 10);

      scope.updateUsageFor(auto_progress, update_amount);
    });
  }
};
