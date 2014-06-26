

Dependencies
==============
1)
django-recaptcha>=0.0.6
2)
django-cities-light>=2.1.8
south
3)
MySQL-python
4)
python-smpplib
Install from github
https://github.com/podshumok/python-smpplib

2)
#dependency of django-cities-light
easy_install south

How to setup
============
a)
CREATE DATABASE horizon CHARACTER SET utf8;

b)
Update openstack_dashboard/local/local_settings.py with following settings

#CREATE DATABASE horizon CHARACTER SET utf8;
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'horizon',
        'USER': 'root',
        'PASSWORD': 'xxxxxx',
        'HOST': '',
        'PORT': '',
    },
}

EMAIL_HOST = "localhost"
EMAIL_PORT = 25

RECAPTCHA_PUBLIC_KEY = 'xxxxxxxxxxx'
RECAPTCHA_PRIVATE_KEY = 'xxxxxxxxxxx'
RECAPTCHA_USE_SSL = False

SMS_SYSTEM_HOSTNAME = 'smpp1.smsapi.org'
SMS_SYSTEM_PORT = 2775
SMS_SYSTEM_ID = 'xxxxxxxxxxx'
SMS_SYSTEM_PASSWORD = 'xxxxxxxxxxx'
SMS_SYSTEM_SOURCE_ADDR = '+912233445566'
SMS_SYSTEM_SMS_TIMEOUT = 300
SMS_SYSTEM_MSG = "Kindly enter following code on your screen to complete the registration - "

SECURITY_SERVICE_HOST = "127.0.0.1"
SECURITY_SERVICE_PORT = 8080

LOGIN_REDIRECT_URL = '/'

SITE_BRANDING = "JioCloud"

THEME_APP = 'horizon_jiocloud'
FORM_APPS = ('captcha', 'cities_light')
try:
    from openstack_dashboard.settings import INSTALLED_APPS
    INSTALLED_APPS = (THEME_APP,) +  FORM_APPS + INSTALLED_APPS
except:
    pass

SITE_URL = "http://127.0.0.1"


# Specify a regular expression to validate user passwords.
HORIZON_CONFIG["password_validator"] = {
    "regex": '^.{6,10}$',
    "help_text": _("Your password does not meet the requirements.")
}

# Send email 
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'


c)
python manage.py syncdb
python manage.py cities_light