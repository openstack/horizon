$(document).ready(function() {
  $(".form-rename button").button();
  // Convert the rename input into a dialog
  $(".form-rename div.network_rename_div").dialog({
      autoOpen : false,
      modal : true,
      draggable : true,
      resizable: false,
      position: 'center',
      title : 'Enter new network name'
  });
  
  // Network rename
  $(".form-rename .rename").click(function() {
      var id = $(this).attr('id');
      id = id.replace(/^rename_/,'');
      // Show the dialog
      $("div#rename_div_"+id).dialog('open');
      
      // Return false here to prevent submitting the form
      return false;
  });
  $("div.network_rename_div .dialog_rename").click(function() {
      var id = $(this).attr('id');
      // Update name
      $('#new_name_'+id).val($('#change_to_'+id).val());
      // Close dialog
      $("div#rename_div_"+id).dialog('close');
      // Submit original form
      $("form#form_rename_"+id).submit();
  });
});
