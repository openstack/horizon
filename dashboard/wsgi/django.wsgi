import logging
import os
import sys
import django.core.handlers.wsgi
from django.conf import settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'dashboard.settings'
sys.stdout = sys.stderr

DEBUG = False

class WSGIRequest(django.core.handlers.wsgi.WSGIRequest):
    def is_secure(self):
        value = self.META.get('wsgi.url_scheme', '').lower()
        if value == 'https':
            return True
        return False

class WSGIHandler(django.core.handlers.wsgi.WSGIHandler):
    request_class = WSGIRequest

_application = WSGIHandler()

def application(environ, start_response):
    environ['PATH_INFO'] = environ['SCRIPT_NAME'] + environ['PATH_INFO']
    environ['wsgi.url_scheme'] = environ.get('HTTP_X_URL_SCHEME', 'http')

    return _application(environ, start_response)

