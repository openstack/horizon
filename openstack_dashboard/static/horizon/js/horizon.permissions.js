/* 
 * AJAX handling for permissions in my applications
 */

horizon.permissions = {
    _loaded_permissions = [], //dictionary to store already loaded permissions
    active_role = null
};

horizon.addInitFunction(function() {

 /*// AJAX loading of the role permissions
  $(document).on('submit', '#create_role_form', function (evt) {
    
    //logic

    ajaxOpts = {
      type: "POST",
      url: $form.attr('action'),
      headers: headers,
      data: formData,
      beforeSend: function () {
        console.log('before send');
      },
      complete: function () {
       
      },
      success: function (data, textStatus, jqXHR) {
        console.log('success');
      },
      error: function (jqXHR, status, errorThrown) {
        console.log('error');
    };

    $.ajax(ajaxOpts);
    console.log('ajax!');
  });*/

});

