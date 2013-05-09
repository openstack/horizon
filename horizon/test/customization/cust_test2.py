import horizon

dogs = horizon.get_dashboard("dogs")

puppies = dogs.get_panel("puppies")

permissions = list(getattr(puppies, 'permissions', []))
permissions.append('horizon.test')
puppies.permissions = tuple(permissions)
