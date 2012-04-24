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

  // Confirmation on deletion of items.
  // TODO (tres): These need to be localizable or to just plain go away in favor
  // of modals.
  $(".terminate").click(function () {
    var response = confirm('Are you sure you want to terminate the Instance: ' + $(this).attr('title') + "?");
    return response;
  });

  $(".delete").click(function (e) {
    var response = confirm('Are you sure you want to delete the ' + $(this).attr('title') + " ?");
    return response;
  });

  $(".reboot").click(function (e) {
    var response = confirm('Are you sure you want to reboot the ' + $(this).attr('title') + " ?");
    return response;
  });

  $(".disable").click(function (e) {
    var response = confirm('Are you sure you want to disable the ' + $(this).attr('title') + " ?");
    return response;
  });

  $(".enable").click(function (e) {
    var response = confirm('Are you sure you want to enable the ' + $(this).attr('title') + " ?");
    return response;
  });

  $(".detach").click(function (e) {
    var response = confirm('Are you sure you want to detach the ' + $(this).attr('title') + " ?");
    return response;
  });

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
    })).change();

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
  $(document).on('change', '.form-field select', function() {
    $(this).tooltip('hide');
  });

  // Hide the text for js-capable browsers
  $('span.help-block').hide();
});

/* Update quota usage infographics when a flavor is selected to show the usage
 * that will be consumed by the selected flavor. */
horizon.updateQuotaUsages = function(flavors, usages) {
  var selectedFlavor = _.find(flavors, function(flavor) {
    return flavor.id == $("#id_flavor").children(":selected").val();
  });

  var selectedCount = parseInt($("#id_count").val());
  if(isNaN(selectedCount)) {
    selectedCount = 1;
  }

  // Map usage data fields to their corresponding html elements
  var flavorUsageMapping = [
    {'usage': 'instances', 'element': 'quota_instances'},
    {'usage': 'cores', 'element': 'quota_cores'},
    {'usage': 'gigabytes', 'element': 'quota_disk'},
    {'usage': 'ram', 'element': 'quota_ram'}
  ];

  var el, used, usage, width;
  _.each(flavorUsageMapping, function(mapping) {
    el = $('#' + mapping.element + " .progress_bar_selected");
    used = 0;
    usage = usages[mapping.usage];

    if(mapping.usage == "instances") {
      used = selectedCount;
    } else {
      _.each(usage.flavor_fields, function(flavorField) {
        used += (selectedFlavor[flavorField] * selectedCount);
      });
    }

    available = 100 - $('#' + mapping.element + " .progress_bar_fill").attr("data-width");
    if(used + usage.used <= usage.quota) {
      width = Math.round((used / usage.quota) * 100);
      el.removeClass('progress_bar_over');
    } else {
      width = available;
      if(!el.hasClass('progress_bar_over')) {
        el.addClass('progress_bar_over');
      }
    }

    el.animate({width: width + "%"}, 300);
  });

  // Also update flavor details
  $("#flavor_name").html(horizon.utils.truncate(selectedFlavor.name, 14, true));
  $("#flavor_vcpus").text(selectedFlavor.vcpus);
  $("#flavor_disk").text(selectedFlavor.disk);
  $("#flavor_ephemeral").text(selectedFlavor["OS-FLV-EXT-DATA:ephemeral"]);
  $("#flavor_disk_total").text(selectedFlavor.disk + selectedFlavor["OS-FLV-EXT-DATA:ephemeral"]);
  $("#flavor_ram").text(selectedFlavor.ram);
};
