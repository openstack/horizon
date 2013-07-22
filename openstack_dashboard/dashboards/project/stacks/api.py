import json
import logging

from openstack_dashboard.api.heat import resources_list
from openstack_dashboard.api.heat import stack_get

from openstack_dashboard.dashboards.project.stacks.mappings \
    import get_resource_image
from openstack_dashboard.dashboards.project.stacks.mappings \
    import get_resource_status
from openstack_dashboard.dashboards.project.stacks.sro import resource_info
from openstack_dashboard.dashboards.project.stacks.sro import stack_info


LOG = logging.getLogger(__name__)


class Stack(object):
    pass


def d3_data(request, stack_id=''):
    try:
        stack = stack_get(request, stack_id)
    except:
        stack = Stack()
        stack.id = stack_id
        stack.stack_name = request.session.get('stack_name', '')
        stack.stack_status = 'DELETE_COMPLETE'
        stack.stack_status_reason = 'DELETE_COMPLETE'

    try:
        resources = resources_list(request, stack.stack_name)
    except:
        resources = []

    d3_data = {"nodes": [], "stack": {}}
    if stack:
        stack_image = get_resource_image(stack.stack_status, 'stack')
        stack_node = {
            'stack_id': stack.id,
            'name': stack.stack_name,
            'status': stack.stack_status,
            'image': stack_image,
            'image_size': 60,
            'image_x': -30,
            'image_y': -30,
            'text_x': 40,
            'text_y': ".35em",
            'in_progress': True if (get_resource_status(stack.stack_status) ==
                                   'IN_PROGRESS') else False,
            'info_box': stack_info(stack, stack_image)
        }
        d3_data['stack'] = stack_node

    if resources:
        for resource in resources:
            resource_image = get_resource_image(resource.resource_status,
                                            resource.resource_type)
            in_progress = True if (
                get_resource_status(resource.resource_status)
                == 'IN_PROGRESS') else False
            resource_node = {
                'name': resource.logical_resource_id,
                'status': resource.resource_status,
                'image': resource_image,
                'required_by': resource.required_by,
                'image_size': 50,
                'image_x': -25,
                'image_y': -25,
                'text_x': 35,
                'text_y': ".35em",
                'in_progress': in_progress,
                'info_box': resource_info(resource)
            }
            d3_data['nodes'].append(resource_node)
    return json.dumps(d3_data)
