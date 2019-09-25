# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import datetime
import logging

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as django_auth_views
from django.contrib import messages
from django import http as django_http
from django import shortcuts
from django.urls import reverse
from django.utils import functional
from django.utils import http
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import edit as edit_views
from keystoneauth1 import exceptions as keystone_exceptions
import six

from openstack_auth import exceptions
from openstack_auth import forms
from openstack_auth import plugin

# This is historic and is added back in to not break older versions of
# Horizon, fix to Horizon to remove this requirement was committed in
# Juno
# pylint: disable=unused-import
from openstack_auth.forms import Login  # noqa:F401
from openstack_auth import user as auth_user
from openstack_auth import utils


LOG = logging.getLogger(__name__)


# TODO(stephenfin): Migrate to CBV
@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request):
    """Logs a user in using the :class:`~openstack_auth.forms.Login` form."""

    # If the user enabled websso and the default redirect
    # redirect to the default websso url
    if (request.method == 'GET' and utils.is_websso_enabled and
            utils.is_websso_default_redirect()):
        protocol = utils.get_websso_default_redirect_protocol()
        region = utils.get_websso_default_redirect_region()
        origin = utils.build_absolute_uri(request, '/auth/websso/')
        url = ('%s/auth/OS-FEDERATION/websso/%s?origin=%s' %
               (region, protocol, origin))
        return shortcuts.redirect(url)

    # If the user enabled websso and selects default protocol
    # from the dropdown, We need to redirect user to the websso url
    if request.method == 'POST':
        auth_type = request.POST.get('auth_type', 'credentials')
        if utils.is_websso_enabled() and auth_type != 'credentials':
            region_id = request.POST.get('region')
            auth_url = getattr(settings, 'WEBSSO_KEYSTONE_URL', None)
            if auth_url is None:
                auth_url = forms.get_region_endpoint(region_id)
            url = utils.get_websso_url(request, auth_url, auth_type)
            return shortcuts.redirect(url)

    if not request.is_ajax():
        # If the user is already authenticated, redirect them to the
        # dashboard straight away, unless the 'next' parameter is set as it
        # usually indicates requesting access to a page that requires different
        # permissions.
        if (request.user.is_authenticated and
                auth.REDIRECT_FIELD_NAME not in request.GET and
                auth.REDIRECT_FIELD_NAME not in request.POST):
            return shortcuts.redirect(settings.LOGIN_REDIRECT_URL)

    # Get our initial region for the form.
    initial = {}
    current_region = request.session.get('region_endpoint', None)
    requested_region = request.GET.get('region', None)
    regions = dict(settings.AVAILABLE_REGIONS)
    if requested_region in regions and requested_region != current_region:
        initial.update({'region': requested_region})

    if request.method == "POST":
        form = functional.curry(forms.Login)
    else:
        form = functional.curry(forms.Login, initial=initial)

    choices = settings.WEBSSO_CHOICES
    extra_context = {
        'redirect_field_name': auth.REDIRECT_FIELD_NAME,
        'csrf_failure': request.GET.get('csrf_failure'),
        'show_sso_opts': utils.is_websso_enabled() and len(choices) > 1,
    }

    if request.is_ajax():
        template_name = 'auth/_login.html'
        extra_context['hide'] = True
    else:
        template_name = 'auth/login.html'

    try:
        res = django_auth_views.LoginView.as_view(
            template_name=template_name,
            redirect_field_name=auth.REDIRECT_FIELD_NAME,
            form_class=form,
            extra_context=extra_context,
            redirect_authenticated_user=False)(request)
    except exceptions.KeystonePassExpiredException as exc:
        res = django_http.HttpResponseRedirect(
            reverse('password', args=[exc.user_id]))
        msg = _("Your password has expired. Please set a new password.")
        res.set_cookie('logout_reason', msg, max_age=10)

    # Save the region in the cookie, this is used as the default
    # selected region next time the Login form loads.
    if request.method == "POST":
        utils.set_response_cookie(res, 'login_region',
                                  request.POST.get('region', ''))
        utils.set_response_cookie(res, 'login_domain',
                                  request.POST.get('domain', ''))

    # Set the session data here because django's session key rotation
    # will erase it if we set it earlier.
    if request.user.is_authenticated:
        auth_user.set_session_from_user(request, request.user)
        regions = dict(forms.get_region_choices())
        region = request.user.endpoint
        login_region = request.POST.get('region')
        region_name = regions.get(login_region)
        request.session['region_endpoint'] = region
        request.session['region_name'] = region_name
        expiration_time = request.user.time_until_expiration()
        threshold_days = settings.PASSWORD_EXPIRES_WARNING_THRESHOLD_DAYS
        if (expiration_time is not None and
                expiration_time.days <= threshold_days and
                expiration_time > datetime.timedelta(0)):
            expiration_time = str(expiration_time).rsplit(':', 1)[0]
            msg = (_('Please consider changing your password, it will expire'
                     ' in %s minutes') %
                   expiration_time).replace(':', ' Hours and ')
            messages.warning(request, msg)
    return res


# TODO(stephenfin): Migrate to CBV
@sensitive_post_parameters()
@csrf_exempt
@never_cache
def websso(request):
    """Logs a user in using a token from Keystone's POST."""
    referer = request.META.get('HTTP_REFERER', settings.OPENSTACK_KEYSTONE_URL)
    auth_url = utils.clean_up_auth_url(referer)
    token = request.POST.get('token')
    try:
        request.user = auth.authenticate(request, auth_url=auth_url,
                                         token=token)
    except exceptions.KeystoneAuthException as exc:
        if utils.is_websso_default_redirect():
            res = django_http.HttpResponseRedirect(settings.LOGIN_ERROR)
        else:
            msg = 'Login failed: %s' % six.text_type(exc)
            res = django_http.HttpResponseRedirect(settings.LOGIN_URL)
            res.set_cookie('logout_reason', msg, max_age=10)
        return res

    auth_user.set_session_from_user(request, request.user)
    auth.login(request, request.user)
    if request.session.test_cookie_worked():
        request.session.delete_test_cookie()
    return django_http.HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)


# TODO(stephenfin): Migrate to CBV
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
    if (utils.is_websso_enabled and utils.is_websso_default_redirect() and
            utils.get_websso_default_redirect_logout()):
        auth_user.unset_session_user_variables(request)
        return django_http.HttpResponseRedirect(
            utils.get_websso_default_redirect_logout())
    else:
        return django_auth_views.logout_then_login(request,
                                                   login_url=login_url,
                                                   **kwargs)


# TODO(stephenfin): Migrate to CBV
@login_required
def switch(request, tenant_id, redirect_field_name=auth.REDIRECT_FIELD_NAME):
    """Switches an authenticated user from one project to another."""
    LOG.debug('Switching to tenant %s for user "%s".',
              tenant_id, request.user.username)

    endpoint, __ = utils.fix_auth_url_version_prefix(request.user.endpoint)
    session = utils.get_session()
    # Keystone can be configured to prevent exchanging a scoped token for
    # another token. Always use the unscoped token for requesting a
    # scoped token.
    unscoped_token = request.user.unscoped_token
    auth = utils.get_token_auth_plugin(auth_url=endpoint,
                                       token=unscoped_token,
                                       project_id=tenant_id)

    try:
        auth_ref = auth.get_access(session)
        msg = 'Project switch successful for user "%(username)s".' % \
            {'username': request.user.username}
        LOG.info(msg)
    except keystone_exceptions.ClientException:
        msg = (
            _('Project switch failed for user "%(username)s".') %
            {'username': request.user.username})
        messages.error(request, msg)
        auth_ref = None
        LOG.exception('An error occurred while switching sessions.')

    # Ensure the user-originating redirection url is safe.
    # Taken from django.contrib.auth.views.login()
    redirect_to = request.GET.get(redirect_field_name, '')
    if not http.is_safe_url(url=redirect_to,
                            allowed_hosts=[request.get_host()]):
        redirect_to = settings.LOGIN_REDIRECT_URL

    if auth_ref:
        user = auth_user.create_user_from_token(
            request,
            auth_user.Token(auth_ref, unscoped_token=unscoped_token),
            endpoint)
        auth_user.set_session_from_user(request, user)
        message = (
            _('Switch to project "%(project_name)s" successful.') %
            {'project_name': request.user.project_name})
        messages.success(request, message)
    response = shortcuts.redirect(redirect_to)
    utils.set_response_cookie(response, 'recent_project',
                              request.user.project_id)
    return response


# TODO(stephenfin): Migrate to CBV
@login_required
def switch_region(request, region_name,
                  redirect_field_name=auth.REDIRECT_FIELD_NAME):
    """Switches the user's region for all services except Identity service.

    The region will be switched if the given region is one of the regions
    available for the scoped project. Otherwise the region is not switched.
    """
    if region_name in request.user.available_services_regions:
        request.session['services_region'] = region_name
        LOG.debug('Switching services region to %s for user "%s".',
                  region_name, request.user.username)

    redirect_to = request.GET.get(redirect_field_name, '')
    if not http.is_safe_url(url=redirect_to,
                            allowed_hosts=[request.get_host()]):
        redirect_to = settings.LOGIN_REDIRECT_URL

    response = shortcuts.redirect(redirect_to)
    utils.set_response_cookie(response, 'services_region',
                              request.session['services_region'])
    return response


# TODO(stephenfin): Migrate to CBV
@login_required
def switch_keystone_provider(request, keystone_provider=None,
                             redirect_field_name=auth.REDIRECT_FIELD_NAME):
    """Switches the user's keystone provider using K2K Federation

    If keystone_provider is given then we switch the user to
    the keystone provider using K2K federation. Otherwise if keystone_provider
    is None then we switch the user back to the Identity Provider Keystone
    which a non federated token auth will be used.
    """
    base_token = request.session.get('k2k_base_unscoped_token', None)
    k2k_auth_url = request.session.get('k2k_auth_url', None)
    keystone_providers = request.session.get('keystone_providers', None)
    recent_project = request.COOKIES.get('recent_project')

    if not base_token or not k2k_auth_url:
        msg = _('K2K Federation not setup for this session')
        raise exceptions.KeystoneAuthException(msg)

    redirect_to = request.GET.get(redirect_field_name, '')
    if not http.is_safe_url(url=redirect_to,
                            allowed_hosts=[request.get_host()]):
        redirect_to = settings.LOGIN_REDIRECT_URL

    unscoped_auth_ref = None
    keystone_idp_id = settings.KEYSTONE_PROVIDER_IDP_ID

    if keystone_provider == keystone_idp_id:
        current_plugin = plugin.TokenPlugin()
        unscoped_auth = current_plugin.get_plugin(auth_url=k2k_auth_url,
                                                  token=base_token)
    else:
        # Switch to service provider using K2K federation
        plugins = [plugin.TokenPlugin()]
        current_plugin = plugin.K2KAuthPlugin()

        unscoped_auth = current_plugin.get_plugin(
            auth_url=k2k_auth_url, service_provider=keystone_provider,
            plugins=plugins, token=base_token, recent_project=recent_project)

    try:
        # Switch to identity provider using token auth
        unscoped_auth_ref = current_plugin.get_access_info(unscoped_auth)
    except exceptions.KeystoneAuthException as exc:
        msg = 'Switching to Keystone Provider %s has failed. %s' \
              % (keystone_provider, (six.text_type(exc)))
        messages.error(request, msg)

    if unscoped_auth_ref:
        try:
            request.user = auth.authenticate(
                request, auth_url=unscoped_auth.auth_url,
                token=unscoped_auth_ref.auth_token)
        except exceptions.KeystoneAuthException as exc:
            msg = 'Keystone provider switch failed: %s' % six.text_type(exc)
            res = django_http.HttpResponseRedirect(settings.LOGIN_URL)
            res.set_cookie('logout_reason', msg, max_age=10)
            return res
        auth.login(request, request.user)
        auth_user.set_session_from_user(request, request.user)
        request.session['keystone_provider_id'] = keystone_provider
        request.session['keystone_providers'] = keystone_providers
        request.session['k2k_base_unscoped_token'] = base_token
        request.session['k2k_auth_url'] = k2k_auth_url
        message = (
            _('Switch to Keystone Provider "%(keystone_provider)s" '
              'successful.') % {'keystone_provider': keystone_provider})
        messages.success(request, message)

    response = shortcuts.redirect(redirect_to)
    return response


class PasswordView(edit_views.FormView):
    """Changes user's password when it's expired or otherwise inaccessible."""
    template_name = 'auth/password.html'
    form_class = forms.Password
    success_url = settings.LOGIN_URL

    def get_initial(self):
        return {'user_id': self.kwargs['user_id']}

    def form_valid(self, form):
        # We have no session here, so regular messages don't work.
        msg = _('Password changed. Please log in to continue.')
        res = django_http.HttpResponseRedirect(self.success_url)
        res.set_cookie('logout_reason', msg, max_age=10)
        return res
