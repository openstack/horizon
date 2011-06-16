# vim: tabstop=4 shiftwidth=4 softtabstop=4

'''
django_openstack logging functions Currently does nothing useful, but if
everything already points here, makes adding more complex logging simpler in
the future
'''

import logging


def getLogger(name):
    '''
    Returns a python logger
    '''
    return logging.getLogger(name)
