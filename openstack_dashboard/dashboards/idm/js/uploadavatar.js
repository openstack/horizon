function readURL(input) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        
        reader.onload = function (e) {
            $('#blah').attr('src', e.target.result);
        }
        
        reader.readAsDataURL(input.files[0]);
    }
    console.log('Hace el cambio');
}

$("#imgInp").change(function(){
	console.log('Entra al cambio');
    readURL(this);
});
    




