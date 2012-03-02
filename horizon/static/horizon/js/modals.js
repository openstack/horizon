horizon.addInitFunction(function() {
  $(document).on('click', '.modal:not(.static_page) .cancel', function (evt) {
    $(this).closest('.modal').modal('hide');
    return false;
  });

  $('.ajax-modal').click(function (evt) {
    var $this = $(this);
    $.ajax($this.attr('href'), {
      error: function(jqXHR, status, errorThrown){
        if (jqXHR.status === 401){
          var redir_url = jqXHR.getResponseHeader("REDIRECT_URL");
          if (redir_url){
            location.href = redir_url;
          } else {
            location.reload(true);
          }
        }
      },
      success: function (data, status, jqXHR) {
        $('body').append(data);
        $('.modal span.help-block').hide();
        $('.modal:last').modal();
        $('.modal:last').on('hidden', function () {
          $(this).remove();
        });

        var $form = $('.modal:last').find('form');
        if($form) {
          var checkboxes = $form.find(":checkbox")
          if(checkboxes.length != 0 && checkboxes.filter(":checked").length == 0) {
            $form.find(".table_actions button.btn-danger").addClass("disabled");
          }
          $form.find(":checkbox").on("click", function (evt) {
            var any_checked = $form.find(":checkbox").is(":checked");
            if(any_checked) {
              $form.find(".table_actions button.btn-danger").removeClass("disabled");
            }else {
              $form.find(".table_actions button.btn-danger").addClass("disabled");
            }
          });
        }

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
      }
    });
    evt.preventDefault();
  });
});
