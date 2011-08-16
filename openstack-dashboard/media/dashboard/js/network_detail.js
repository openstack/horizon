$(document).ready(function() {
  $(".form-attach button").button();
  // Convert attach port into a dialog
  $(".form-attach div.port-attach").dialog({
      autoOpen : false,
      modal : true,
      draggable : true,
      resizable: false,
      position: 'center',
      title : 'Select virtual interface'
  });
  // Port attach
  $(".form-attach .attach").click(function() {
        var id = $(this).attr('id');
        id = id.replace(/^attach_/,'');
        // Hide error
        $("div#port_attach_div_"+id+" div.error_block").hide();
        // Remove select
        $("div#port_attach_div_"+id+" select").remove();
        // Show status
        $("div#port_attach_div_"+id+" div.vif_status").show();
        // Clear out the values table
        $("div#port_attach_div_"+id+" td.row_val").html('-');
        // Hide the submit button
        $("div#port_attach_div_"+id+" .attach_port_button").hide();
        // Fetch interfaces from the server
        $.ajax({
            url     : '/ajax/virtual_interfaces',
            type    : 'GET',
            success : function(msg) {
                // Hide status
                $("div#port_attach_div_"+id+" div.vif_status").hide(100);
                if ( $.isArray(msg) ) {
                    if (msg.length == 0) {
                        // No interfaces found, show message
                        $("div#port_attach_div_"+id+" div.error_block")
                            .html('No virtual interfaces found.')
                            .show(100);
                        return false;
                    }
                    $("div#port_attach_div_"+id+" .attach_port_button").show();
                    // Create a select box
                    $("div#port_attach_div_"+id+" div.select_area")
                        .append($('<select></select>')
                        .addClass('vif-list'));
                    // Add an empty option on top
                    $("div#port_attach_div_"+id+" select")
                            .append($('<option></option>')
                            .attr('value','')
                            .text('')
                            .attr('selected','selected')
                            .addClass('attach_option'));
                    // Update select values
                    for (i=0; i < msg.length; i++) {
                        if (msg[i].available) {
                            // Append option to select box
                            text = msg[i].instance_name + ' VIF ' + msg[i].id;
                            $("div#port_attach_div_"+id+" select")
                                .append($('<option></option>')
                                .attr('value',msg[i].id)
                                .text(text)
                                .addClass('attach_option'));
                        }
                    }
                    // Show details table
                     $("div#port_attach_div_"+id+" table").show();
                    // Install click handlers for select options
                    $("div#port_attach_div_"+id+" select").change(function() {
                        var selected = $("div#port_attach_div_"+id+" select.vif-list option:selected").val();
                        for (i=0; i < msg.length; i++) {
                            if (msg[i].id == selected) {
                                $("div#port_attach_div_"+id+" td.instance_name").html(msg[i].instance_name);
                                $("div#port_attach_div_"+id+" td.instance_id").html(msg[i].instance);
                                $("div#port_attach_div_"+id+" td.vif_id").html(msg[i].id);
                                $("div#port_attach_div_"+id+" td.network").html(msg[i].network_name);
                            }
                        }
                    });
                } else {
                    // Show error message
                    $("div#port_attach_div_"+id+" div.error_block")
                        .html('Error fetching virtual interface ids: ' + msg)
                        .show(100);
                }
            },
            failure : function(request, msg) {
                $("div#port_attach_div_"+id+" div.vif_status").hide();
                // Show error message
                $("div#port_attach_div_"+id+" div.error_block")
                    .html('Error fetching virtual interface ids: ' + msg)
                    .show(100);
            }
        });
      
        // Show the dialog
        $("div#port_attach_div_"+id).dialog('open');
        // Return false here to prevent submitting the form
        return false;
    });
    $("button.attach_port_button").click(function() {
        var id = $(this).attr('id');
        // Check if we have a vif 
        var val = $("div#port_attach_div_"+id+" select.vif-list option:selected").val();
        if (val) {
            // Append value to form
            $('form#attach_port_form_' + id+ ' input.vif_input').val(val);
            $('form#attach_port_form_' + id).submit();
        } else {
            $("div#port_attach_div_"+id+" div.error_block")
                .html('Please select a virtual interface')
                .show(100);
        }
    });
});
