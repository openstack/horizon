""" Standardized exception classes for the OpenStack Dashboard. """

from novaclient import exceptions as nova_exceptions


class Unauthorized(nova_exceptions.Unauthorized):
    """ A wrapper around novaclient's Unauthorized exception. """
    pass
