from django import template
from django import http
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from glance.client import ClientConnectionError as GlanceClientConnectionError
from glance.common import exception as glance_exception

from django_openstack import api
from django_openstack import forms


@login_required
def index(request):
    images = []
    try:
        images = api.glance_api(request).get_images_detailed()
        if not images:
            messages.info(request, "There are currently no images.")
    except GlanceClientConnectionError, e:
        messages.error(request, "Error connecting to glance: %s" % e.message)
    except glance_exception.Error, e:
        messages.error(request, "Error retrieving image list: %s" % e.message)

    return render_to_response('syspanel_images.html', {
        'images': images,
    }, context_instance = template.RequestContext(request))


@login_required
def delete(request, image_id):
    try:
        glance_api(request).delete_image(image_id)
    except GlanceClientConnectionError, e:
        messages.error(request, "Error connecting to glance: %s" % e.message)
    except glance_exception.Error, e:
        messages.error(request, "Error deleting image: %s" % e.message)
    return redirect('syspanel_images')


@login_required
def toggle(request, image_id):
    try:
        glance_api(request).update_image(image_id, image_meta={'is_public': False})
    except GlanceClientConnectionError, e:
        messages.error(request, "Error connecting to glance: %s" % e.message)
    except glance_exception.Error, e:
        messages.error(request, "Error updating image: %s" % e.message)
    return redirect('syspanel_images')


@login_required
def update(request, image_id):
    try:
        image = glance_api(request).get_image(image_id)[0]
    except GlanceClientConnectionError, e:
        messages.error(request, "Error connecting to glance: %s" % e.message)
    except glance_exception.Error, e:
        messages.error(request, "Error retrieving image %s: %s" % (image_id, e.message))

    if request.method == "POST":
        form = UpdateImageForm(request.POST)
        if form.is_valid():
            image_form = form.clean()
            metadata = {
                'is_public': image_form['is_public'],
                'disk_format': image_form['disk_format'],
                'container_format': image_form['container_format'],
                'name': image_form['name'],
                'location': image_form['location'],
            }
            try:
                # TODO add public flag to properties
                metadata['properties'] = {
                    'kernel_id': int(image_form['kernel_id']),
                    'ramdisk_id': int(image_form['ramdisk_id']),
                    'image_state': image_form['state'],
                    'architecture': image_form['architecture'],
                    'project_id': image_form['project_id'],
                }

                glance_api(request).update_image(image_id, metadata)
                messages.success(request, "Image was successfully updated.")
            except GlanceClientConnectionError, e:
                messages.error(request, "Error connecting to glance: %s" % e.message)
            except glance_exception.Error, e:
                messages.error(request, "Error updating image: %s" % e.message)
            except:
                messages.error(request, "Image could not be updated, please try again.")


        else:
            messages.error(request, "Image could not be uploaded, please try agian.")
            form = UpdateImageForm(request.POST)
            return render_to_response('django_nova_syspanel/images/image_update.html',{
                'image': image,
                'form': form,
            }, context_instance = template.RequestContext(request))

        return redirect('syspanel_images')
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

        return render_to_response('django_nova_syspanel/images/image_update.html',{
            'image': image,
            'form': form,
        }, context_instance = template.RequestContext(request))

@login_required
def upload(request):
    if request.method == "POST":
        form = UploadImageForm(request.POST)
        if form.is_valid():
            image = form.clean()
            metadata = {'is_public': image['is_public'],
                        'disk_format': 'ami',
                        'container_format': 'ami',
                        'name': image['name']}
            try:
                messages.success(request, "Image was successfully uploaded.")
            except:
                # TODO add better error management
                messages.error(request, "Image could not be uploaded, please try again.")

            try:
                glance_api(request).add_image(metadata, image['image_file'])
            except GlanceClientConnectionError, e:
                messages.error(request, "Error connecting to glance: %s" % e.message)
            except glance_exception.Error, e:
                messages.error(request, "Error adding image: %s" % e.message)
        else:
            messages.error(request, "Image could not be uploaded, please try agian.")
            form = UploadImageForm(request.POST)
            return render_to_response('django_nova_syspanel/images/image_upload.html',{
                'form': form,
            }, context_instance = template.RequestContext(request))

        return redirect('syspanel_images')
    else:
        form = UploadImageForm()
        return render_to_response('django_nova_syspanel/images/image_upload.html',{
            'form': form,
        }, context_instance = template.RequestContext(request))
