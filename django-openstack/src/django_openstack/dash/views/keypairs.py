class DeleteKeypair(forms.SelfHandlingForm):
    keypair_id = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            keypair = extras_api(request).keypairs.delete(data['keypair_id'])
        except api_exceptions.ApiException, e:
            messages.error(request, 'Error deleting keypair: %s' % e.message)
        return redirect('dash_keypairs')

class CreateKeypair(forms.SelfHandlingForm):
    name = forms.CharField(max_length="20", label="Keypair Name")

    def handle(self, request, data):
        try:
            keypair = extras_api(request).keypairs.create(data['name'])
            response = http.HttpResponse(mimetype='application/binary')
            response['Content-Disposition'] = \
                'attachment; filename=%s.pem' % \
                keypair.key_name
            response.write(keypair.private_key)
            return response
        except api_exceptions.ApiException, e:
            messages.error(request, 'Error Creating Keypair: %s' % e.message)
            return redirect('dash_keypairs')

@login_required
def index(request):
    for f in (DeleteKeypair):
        _, handled = f.maybe_handle(request)
        if handled:
            return handled

    delete_form = DeleteKeypair()

    try:
        keypairs = extras_api(request).keypairs.list()
    except api_exceptions.ApiException, e:
        keypairs = []
        messages.error(request, 'Error featching keypairs: %s' % e.message)

    return render_to_response('dash_keypairs.html', {
        'keypairs': keypairs,
        'delete_form': delete_form,
    }, context_instance=template.RequestContext(request))

@login_required
def keypair_create(request):
    form, handled = CreateKeypair.maybe_handle(request)
    if handled:
        return handled

    return render_to_response('keypair_create.html', {
        'create_form': form,
    }, context_instance=template.RequestContext(request))
