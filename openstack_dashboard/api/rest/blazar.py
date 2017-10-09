from django.views import generic

from openstack_dashboard import api
from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils

from blazar_dashboard.api.client import lease_list


@urls.register
class Reservations(generic.View):
    """Mini-API for Blazar (things Nova needs to know)
    """
    url_regex = r'blazar/reservations/$'

    @rest_utils.ajax()
    def get(self, request):
        """List active physical-host reservations.
        """
        if api.base.is_service_enabled(request, 'reservation'):
            leases = lease_list(request)
            reservations = []
            for lease in leases:
                lease = lease.to_dict()
                lease_reservations = [
                    r
                    for r
                    in lease['reservations']
                    if (r['status'] == 'active'
                        and r['resource_type'] == 'physical:host')
                ]
                for r in lease_reservations:
                    r['lease_name'] = lease['name']
                reservations.extend(lease_reservations)
            return {'reservations': reservations}
        else:
            raise rest_utils.AjaxError(501, '')
