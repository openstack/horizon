import logging
import traceback

LOG = logging.getLogger('openstack_dashboard')


class DashboardLogUnhandledExceptionsMiddleware(object):
    def process_exception(self, request, exception):
        tb_text = traceback.format_exc()
        LOG.critical('Unhandled Exception in dashboard. Exception "%s"'
                     '\n%s' % (str(exception), tb_text))
