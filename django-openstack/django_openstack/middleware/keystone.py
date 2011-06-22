# vim: tabstop=4 shiftwidth=4 softtabstop=4
from django.contrib import messages
from django import shortcuts
import openstackx
import openstack


class User(object):
    def __init__(self, token, user, tenant, admin):
        self.token = token
        self.username = user
        self.tenant = tenant
        self.admin = admin

    def is_authenticated(self):
        # TODO: deal with token expiration
        return self.token

    def is_admin(self):
        return self.admin


def get_user_from_request(request):
    if 'user' not in request.session:
        return User(None,None,None,None)
    return User(request.session['token'],
                request.session['user'],
                request.session['tenant'],
                request.session['admin'])


class LazyUser(object):
    def __get__(self, request, obj_type=None):
        if not hasattr(request, '_cached_user'):
            request._cached_user = get_user_from_request(request)
        return request._cached_user


class AuthenticationMiddleware(object):
    def process_request(self, request):
        request.__class__.user = LazyUser()

    def process_exception(self, request, exception):
        if type(exception) in [openstack.compute.exceptions.Forbidden,
                               openstackx.api.exceptions.Forbidden,
                               #BEWARE - had to add this exception handler
                               # to make token expiration work
                               openstackx.api.exceptions.NotFound]:
            messages.error(request, 'Your token has expired.\
                                     Please log in again')
            return shortcuts.redirect('/auth/logout')
