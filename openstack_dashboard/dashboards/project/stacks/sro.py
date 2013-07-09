from django.template.defaultfilters import title
from django.template.loader import render_to_string

from horizon.utils.filters import replace_underscores


def stack_info(stack, stack_image):
    stack.stack_status_desc = title(replace_underscores(stack.stack_status))
    if stack.stack_status_reason:
        stack.stack_status_reason = title(
            replace_underscores(stack.stack_status_reason)
        )
    context = {}
    context['stack'] = stack
    context['stack_image'] = stack_image
    return render_to_string('project/stacks/_stack_info.html',
                            context)


def resource_info(resource):
    resource.resource_status_desc = title(
        replace_underscores(resource.resource_status)
    )
    if resource.resource_status_reason:
        resource.resource_status_reason = title(
            replace_underscores(resource.resource_status_reason)
        )
    context = {}
    context['resource'] = resource
    return render_to_string('project/stacks/_resource_info.html',
                            context)
