
from django_openstack import api


def tenants(request):
  if not request.user:
    return {}
  return {'tenants': api.auth_api().tenants.for_token(request.user.token)}
