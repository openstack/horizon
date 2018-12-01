# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import logging
import os
import random
import string

from oslo_concurrency import lockutils


class FilePermissionError(Exception):
    """The key file permissions are insecure."""


def generate_key(key_length=64):
    """Secret key generator.

    The quality of randomness depends on operating system support,
    see http://docs.python.org/library/random.html#random.SystemRandom.
    """
    if hasattr(random, 'SystemRandom'):
        logging.info('Generating a secure random key using SystemRandom.')
        choice = random.SystemRandom().choice
    else:
        msg = "WARNING: SystemRandom not present. Generating a random "\
              "key using random.choice (NOT CRYPTOGRAPHICALLY SECURE)."
        logging.warning(msg)
        choice = random.choice
    return ''.join(map(lambda x: choice(string.digits + string.ascii_letters),
                   range(key_length)))


def read_from_file(key_file='.secret_key'):
    if (os.stat(key_file).st_mode & 0o777) != 0o600:
        raise FilePermissionError(
            "Insecure permissions on key file %s, should be 0600." %
            os.path.abspath(key_file))
    with open(key_file, 'r') as f:
        key = f.readline()
        return key


def generate_or_read_from_file(key_file='.secret_key', key_length=64):
    """Multiprocess-safe secret key file generator.

    Useful to replace the default (and thus unsafe) SECRET_KEY in settings.py
    upon first start. Save to use, i.e. when multiple Python interpreters
    serve the dashboard Django application (e.g. in a mod_wsgi + daemonized
    environment).  Also checks if file permissions are set correctly and
    throws an exception if not.
    """
    abspath = os.path.abspath(key_file)
    # check, if key_file already exists
    # if yes, then just read and return key
    if os.path.exists(key_file):
        key = read_from_file(key_file)
        return key

    # otherwise, first lock to make sure only one process
    lock = lockutils.external_lock(key_file + ".lock",
                                   lock_path=os.path.dirname(abspath))
    with lock:
        if not os.path.exists(key_file):
            key = generate_key(key_length)
            old_umask = os.umask(0o177)  # Use '0600' file permissions
            with open(key_file, 'w') as f:
                f.write(key)
            os.umask(old_umask)
        else:
            key = read_from_file(key_file)
        return key
