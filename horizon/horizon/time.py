import datetime


def time(hour=0, minute=0, second=0, microsecond=0):
    '''Overrideable version of datetime.datetime.today'''
    if time.override_time:
        return time.override_time
    return datetime.time(hour, minute, second, microsecond)

time.override_time = None


def today():
    '''Overridable version of datetime.datetime.today'''
    if today.override_time:
        return today.override_time
    return datetime.date.today()

today.override_time = None


def utcnow():
    '''Overridable version of datetime.datetime.utcnow'''
    if utcnow.override_time:
        return utcnow.override_time
    return datetime.datetime.utcnow()

utcnow.override_time = None
