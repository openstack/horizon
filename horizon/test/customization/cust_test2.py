import horizon
from horizon import base

try:
    dogs = horizon.get_dashboard("dogs")
    puppies = dogs.get_panel("puppies")
except base.NotRegistered:
    puppies = None

if puppies:
    permissions = list(getattr(puppies, 'permissions', []))
    permissions.append('horizon.test')
    puppies.permissions = tuple(permissions)
