horizon.modals.success = function (data, textStatus, jqXHR) {
  $('body').append(data);
  $('.modal span.help-block').hide();
  $('.modal:last').modal();

  horizon.datatables.validate_button();

  // TODO(tres): Find some better way to deal with grouped form fields.
  var volumeField = $("#id_volume");
  if(volumeField) {
    var volumeContainer = volumeField.parent().parent();
    var deviceContainer = $("#id_device_name").parent().parent();
    var deleteOnTermContainer = $("#id_delete_on_terminate").parent().parent();

    function toggle_fields(show) {
      if(show) {
        volumeContainer.removeClass("hide");
        deviceContainer.removeClass("hide");
        deleteOnTermContainer.removeClass("hide");
      } else {
        volumeContainer.addClass("hide");
        deviceContainer.addClass("hide");
        deleteOnTermContainer.addClass("hide");
      }
    }

    if(volumeField.find("option").length == 1) {
      toggle_fields(false);
    } else {
      var disclosureElement = $("<div />").addClass("volume_boot_disclosure").text("Boot From Volume");

      volumeContainer.before(disclosureElement);

      disclosureElement.click(function() {
        if(volumeContainer.hasClass("hide")) {
          disclosureElement.addClass("on");
          toggle_fields(true);
        } else {
          disclosureElement.removeClass("on");
          toggle_fields(false);
        }
      });

      toggle_fields(false);
    }
  }
};

horizon.addInitFunction(function() {
  $(document).on('click', '.modal:not(.static_page) .cancel', function (evt) {
    $(this).closest('.modal').modal('hide');
    return false;
  });

  $(document).on('submit', '.modal:not(.static_page) form', function (evt) {
    var $form = $(this);
    evt.preventDefault();
    $.ajax({
      type: "POST",
      url: $form.attr('action'),
      data: $form.serialize(),
      success: function (data, textStatus, jqXHR) {
        // TODO(gabriel): This isn't a long-term solution for AJAX redirects.
        // https://blueprints.launchpad.net/horizon/+spec/global-ajax-communication
        var header = jqXHR.getResponseHeader("X-Horizon-Location");
        if (header) {
          location.href = header;
        }
        $form.closest(".modal").modal("hide");
        horizon.modals.success(data, textStatus, jqXHR);
      },
      error: function(jqXHR, status, errorThrown) {
        $form.closest(".modal").modal("hide");
        horizon.alert("error", "There was an error submitting the form. Please try again.");
      }
    });
  });

  // Handle all modal hidden event to remove them as default
  $(document).on('hidden', '.modal', function () {
    $(this).remove();
  });

  $(document).on('show', '.modal', function(evt) {
    var scrollShift = $('body').scrollTop();
    var topVal = $(this).css('top');
    $(this).css('top', scrollShift + parseInt(topVal, 10));
  });

  $('.ajax-modal').click(function (evt) {
    var $this = $(this);
    $.ajax($this.attr('href'), {
      error: function(jqXHR, status, errorThrown) {
        if (jqXHR.status === 401){
          var redir_url = jqXHR.getResponseHeader("X-Horizon-Location");
          if (redir_url){
            location.href = redir_url;
          } else {
            location.reload(true);
          }
        }
      },
      success: horizon.modals.success
    });
    evt.preventDefault();
  });
});
