from django.dispatch import receiver
import django.dispatch

module_handler = django.dispatch.Signal(providing_args=['foo'])

@receiver(module_handler)
def my_callback(sender, **kwargs):
    print "########################################################!"
    print kwargs['foo']
    print "########################################################!"



class DashModule(object):

    def send_signal(self, foo):
        module_handler.send(sender=self, foo=foo)
