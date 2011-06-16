$(function(){
// update/create image form
  $("#images_form input#id_name").example("ami-ubuntu");
  $("#images_form input#id_kernel").example("123");
  $("#images_form input#id_ramdisk").example("123");
  $("#images_form input#id_state").example("available");
  $("#images_form input#id_location").example("file:///var/lib/glance/images/123");
  $("#images_form input#id_architecture").example("x86_64");
  $("#images_form input#id_project_id").example("some");
  $("#images_form input#id_disk_format").example("ari");
  $("#images_form input#id_container_format").example("ari");
  $("#images_form input#id_ramdisk").example("123");

// launch instance form
  $("#launch_img input#id_name").example("YetAnotherInstance")
    
// create flavor form
  $("#flavor_form input#id_flavorid").example("1234");
  $("#flavor_form input#id_name").example("small");
  $("#flavor_form input#id_vcpus").example("256");
  $("#flavor_form input#id_memory_mb").example("256");
  $("#flavor_form input#id_disk_gb").example("256");

// update/create tenant
  $("#tenant_form input#id__id").example("YetAnotherTenant");
  $("#tenant_form textarea#id_description").example("One or two sentence description.");

// table search box
  $("input#table_search").example("Search...")
})