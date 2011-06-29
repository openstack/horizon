# vim: tabstop=4 shiftwidth=4 softtabstop=4

from django import template
from django import http
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from glance.common import exception as glance_exception

from django_openstack import api
from django_openstack import forms


class DeleteImage(forms.SelfHandlingForm):
    image_id = forms.CharField(required=True)

    def handle(self, request, data):
        image_id = data['image_id']
        try:
            api.image_delete(request, image_id)
        except glance_exception.ClientConnectionError, e:
            messages.error(request, "Error connecting to glance: %s" % e.message)
        except glance_exception.Error, e:
            messages.error(request, "Error deleting image: %s" % e.message)
        return redirect(request.build_absolute_uri())


class ToggleImage(forms.SelfHandlingForm):
    image_id = forms.CharField(required=True)

    def handle(self, request, data):
        image_id = data['image_id']
        try:
            api.image_update(request, image_id, image_meta={'is_public': False})
        except glance_exception.ClientConnectionError, e:
            messages.error(request, "Error connecting to glance: %s" % e.message)
        except glance_exception.Error, e:
            messages.error(request, "Error updating image: %s" % e.message)
        return redirect(request.build_absolute_uri())

class UpdateImageForm(forms.Form):
    name = forms.CharField(max_length="5", label="Name")
    kernel = forms.CharField(max_length="5", label="Kernel ID", required=False)
    ramdisk = forms.CharField(max_length="5", label="Ramdisk ID", required=False)
    architecture = forms.CharField(label="Architecture", required=False)
    #project_id = forms.CharField(label="Project ID")
    container_format = forms.CharField(label="Container Format", required=False)
    disk_format = forms.CharField(label="Disk Format")
    #is_public = forms.BooleanField(label="Publicly Available", required=False)

class UploadImageForm(forms.Form):
    name = forms.CharField(max_length="5", label="Name")
    image_file = forms.FileField(required=False)
    # is_public = forms.BooleanField(label="Publicly Available", required=False, initial=True)


@login_required
def index(request):
    for f in (DeleteImage, ToggleImage):
        _, handled = f.maybe_handle(request)
        if handled:
            return handled

    # We don't have any way of showing errors for these, so don't bother
    # trying to reuse the forms from above
    delete_form = DeleteImage()
    toggle_form = ToggleImage()

    images = []
    try:
        images = api.image_list_detailed(request)
        if not images:
            messages.info(request, "There are currently no images.")
    except glance_exception.ClientConnectionError, e:
        messages.error(request, "Error connecting to glance: %s" % e.message)
    except glance_exception.Error, e:
        messages.error(request, "Error retrieving image list: %s" % e.message)

    return render_to_response('syspanel_images.html', {
        'delete_form': delete_form,
        'toggle_form': toggle_form,
        'images': images,
    }, context_instance = template.RequestContext(request))


@login_required
def update(request, image_id):
    try:
        image = api.image_get(request, image_id)
    except glance_exception.ClientConnectionError, e:
        messages.error(request, "Error connecting to glance: %s" % e.message)
    except glance_exception.Error, e:
        messages.error(request, "Error retrieving image %s: %s" % (image_id, e.message))

    if request.method == "POST":
        form = UpdateImageForm(request.POST)
        if form.is_valid():
            image_form = form.clean()
            metadata = {
                'is_public': True,
                'disk_format': image_form['disk_format'],
                'container_format': image_form['container_format'],
                'name': image_form['name'],
            }
            try:
                # TODO add public flag to properties
                metadata['properties'] = {}
                if image_form['kernel']:
                    metadata['properties']['kernel_id'] = image_form['kernel']
                if image_form['ramdisk']:
                    metadata['properties']['ramdisk_id'] = image_form['ramdisk']
                if image_form['architecture']:
                    metadata['properties']['architecture'] = image_form['architecture']
                api.image_update(request, image_id, metadata)
                messages.success(request, "Image was successfully updated.")
            except glance_exception.ClientConnectionError, e:
                messages.error(request, "Error connecting to glance: %s" % e.message)
            except glance_exception.Error, e:
                messages.error(request, "Error updating image: %s" % e.message)
            return redirect("syspanel_images")
        else:
            messages.error(request, "Image could not be uploaded, please try agian.")
            form = UpdateImageForm(request.POST)
            return render_to_response('syspanel_image_update.html',{
                'image': image,
                'form': form,
            }, context_instance = template.RequestContext(request))
    else:
        form = UpdateImageForm(initial={
                'name': image.get('name', ''),
                'kernel': image['properties'].get('kernel_id', ''),
                'ramdisk': image['properties'].get('ramdisk_id', ''),
                'is_public': image.get('is_public', ''),
                'location': image.get('location', ''),
                'state': image['properties'].get('image_state', ''),
                'architecture': image['properties'].get('architecture', ''),
                'project_id': image['properties'].get('project_id', ''),
                'container_format': image.get('container_format', ''),
                'disk_format': image.get('disk_format', ''),
            })

        return render_to_response('syspanel_image_update.html',{
            'image': image,
            'form': form,
        }, context_instance = template.RequestContext(request))

@login_required
def upload(request):
    if request.method == "POST":
        form = UploadImageForm(request.POST)
        if form.is_valid():
            image = form.clean()
            metadata = {'is_public': True,
                        'disk_format': 'ami',
                        'container_format': 'ami',
                        'name': image.get('name', None)}
            try:
                api.image_create(request, metadata, image['image_file'])
            except glance_exception.ClientConnectionError, e:
                messages.error(request, "Error connecting to glance: %s" % e.message)
            except glance_exception.Error, e:
                messages.error(request, "Error adding image: %s" % e.message)
        else:
            messages.error(request, "Image could not be uploaded, please try agian.")
            form = UploadImageForm(request.POST)
            return render_to_response('syspanel_image_upload.html',{
                'form': form,
            }, context_instance = template.RequestContext(request))

        return redirect('syspanel_images')
    else:
        form = UploadImageForm()
        return render_to_response('syspanel_image_upload.html',{
            'form': form,
        }, context_instance = template.RequestContext(request))
