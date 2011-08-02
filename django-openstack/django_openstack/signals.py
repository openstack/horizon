import django.dispatch
from django.dispatch import receiver

dash_apps_ping = django.dispatch.Signal()
dash_apps_urls = django.dispatch.Signal()


def dash_apps_detection():
    """
    Sends a pinging signal to the app, all listening modules will reply with
    items for the sidebar.
    """
    return dash_apps_ping.send(sender=dash_apps_ping)


def dash_app_setup_urls():
    """
    Adds urls from modules
    """
    response = dash_apps_urls.send(senter=dash_apps_urls)
    
    return response


