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
import six

LOG = logging.getLogger(__name__)

@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request, template_name=None, extra_context=None, **kwargs):
    if not request.user.is_authenticated():
        host = getattr(settings, 'SSO_CALLBACK_HOST', None)
        cc_portal_url = getattr(settings, 'CHAMELEON_PORTAL_SSO_BASE_URL', None) + getattr(settings, 'CHAMELEON_PORTAL_SSO_LOGIN_PATH', None)
        if(host is None or cc_portal_url is None):
            LOG.error('Misconfigured CC Portal SSO, settings:, '
                + 'CHAMELEON_PORTAL_SSO_URL: ' + str(cc_portal_url) + ', SSO_CALLBACK_HOST: ' + str(host))
            raise Exception('SSO Login Error')
        login_url = cc_portal_url + '?host=' + host
        if request.GET.get('next'):
            login_url += '&next=' + request.GET.get('next')
        if getattr(settings, 'WEBROOT', None) and getattr(settings, 'WEBROOT', None) != '/':
            login_url += '&webroot=' + getattr(settings, 'WEBROOT', '')
        return django_http.HttpResponseRedirect(login_url)
    return openstack_auth.views.login(request, template_name=None, extra_context=None, **kwargs)

@sensitive_post_parameters()
@csrf_exempt
@never_cache
def cc_websso(request):
    """Logs a user in using a token from Keystone's POST."""
    request.META['HTTP_REFERER'] = settings.OPENSTACK_KEYSTONE_URL
    referer = settings.OPENSTACK_KEYSTONE_URL
    LOG.info(referer)
    auth_url = utils.clean_up_auth_url(referer)
    token = request.POST.get('token')
    LOG.info('token: ' + token)
    try:
        request.user = auth.authenticate(request=request, auth_url=auth_url, token=token)
    except exceptions.KeystoneAuthException as exc:
        # logger.error('Login failed: %s' % six.text_type(exc))
        # raise exc
        msg = 'Login failed: %s' % six.text_type(exc)
        res = django_http.HttpResponseRedirect(settings.LOGOUT_URL)
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
    cc_logout_url = getattr(settings, 'CHAMELEON_PORTAL_SSO_BASE_URL', 'https://www.chameleoncloud.org') \
        + getattr(settings, 'CHAMELEON_PORTAL_SSO_LOGOUT_PATH', '/logout/')
    extra_context = {'cc_logout_url': cc_logout_url}

    """ Securely logs a user out. """
    return django_auth_views.logout(request, template_name='auth/logout.html', extra_context=extra_context)
