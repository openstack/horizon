import logging

LOG = logging.getLogger('openstack_dashboard')


class DashboardLogUnhandledExceptionsMiddleware(object):
    def process_exception(self, request, exception):
        LOG.critical('Unhandled Exception in of type "%s" in dashboard.'
                     % type(exception), exc_info=True)
