import django.dispatch
from django.dispatch import receiver

dash_modules_ping = django.dispatch.Signal()
dash_modules_urls = django.dispatch.Signal()


def dash_modules_detect():
    """
    Sends a pinging signal to the app, all listening modules will reply with
    items for the sidebar.
    
    The response is a tuple of the Signal object instance, and a dictionary.
    The values within the dictionary containing links and a title which should
    be added to the sidebar navigation.
    
    Example: (<dash_apps_ping>,
              {'title': 'Nixon', 
               'links': [{'url':'/syspanel/nixon/google', 
                          'text':'Google', 'active_text': 'google'}],
               'type': syspanel})
    """
    return dash_modules_ping.send(sender=dash_modules_ping)


def dash_app_setup_urls():
    """
    Adds urls from modules
    """
    return dash_modules_urls.send(sender=dash_modules_urls)


