import logging
from django.contrib import auth
from django.contrib.auth import views as django_auth_views
from django.conf import settings
from django import http as django_http
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from openstack_auth import utils
from openstack_auth import exceptions
from openstack_auth import user as auth_user
# from openstack_auth import views

LOG = logging.getLogger(__name__)

@sensitive_post_parameters()
@csrf_exempt
@never_cache
def cc_websso(request):
    print('######################## HTTP_REFERER= ' + request.META['HTTP_REFERER'])
    """Logs a user in using a token from Keystone's POST."""
    request.META['HTTP_REFERER'] = settings.OPENSTACK_KEYSTONE_URL
    referer = settings.OPENSTACK_KEYSTONE_URL
    LOG.info(referer)
    auth_url = utils.clean_up_auth_url(referer)
    LOG.info('auth url: ' + auth_url)
    token = request.POST.get('token')
    LOG.info('token: ' + token)
    try:
        request.user = auth.authenticate(request=request, auth_url=auth_url,
                                         token=token)
    except exceptions.KeystoneAuthException as exc:
        msg = 'Login failed: %s' % six.text_type(exc)
        res = django_http.HttpResponseRedirect(settings.LOGIN_URL)
        res.set_cookie('logout_reason', msg, max_age=10)
        return res

    auth_user.set_session_from_user(request, request.user)
    auth.login(request, request.user)
    if request.session.test_cookie_worked():
        request.session.delete_test_cookie()

    if request.GET.get('next'):
        return django_http.HttpResponseRedirect(request.GET.get('next'))
    return django_http.HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)


def logout(request, login_url=None, **kwargs):
    """Logs out the user if he is logged in. Then redirects to the log-in page.

    :param login_url:
        Once logged out, defines the URL where to redirect after login

    :param kwargs:
        see django.contrib.auth.views.logout_then_login extra parameters.

    """
    msg = 'Logging out user "%(username)s".' % \
        {'username': request.user.username}
    LOG.info(msg)

    """ Securely logs a user out. """
    return django_auth_views.logout(request, template_name='auth/logout.html')