# vim: tabstop=4 shiftwidth=4 softtabstop=4


class User(object):
    def __init__(self, token, user, tenant, admin):
        self.token = token
        self.username = user
        self.tenant = tenant
        self.admin = admin

    def is_authenticated(self):
        return True

    def is_admin(self):
        return self.admin


def get_user_from_request(request):
    if 'user' not in request.session:
        return None
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

