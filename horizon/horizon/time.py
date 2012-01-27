import datetime


def time():
    '''Overrideable version of datetime.datetime.today'''
    if time.override_time:
        return time.override_time
    return datetime.time()

time.override_time = None


def today():
    '''Overridable version of datetime.datetime.today'''
    if today.override_time:
        return today.override_time
    return datetime.datetime.today()

today.override_time = None


def utcnow():
    '''Overridable version of datetime.datetime.utcnow'''
    if utcnow.override_time:
        return utcnow.override_time
    return datetime.datetime.utcnow()

utcnow.override_time = None
