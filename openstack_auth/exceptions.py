# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.


class KeystoneAuthException(Exception):
    """Generic error class to identify and catch our own errors."""


class KeystoneTokenExpiredException(KeystoneAuthException):
    """The authentication token issued by the Identity service has expired."""


class KeystoneNoBackendException(KeystoneAuthException):
    """No backend could be determined to handle the provided credentials."""


class KeystoneNoProjectsException(KeystoneAuthException):
    """You are not authorized for any projects or domains."""


class KeystoneRetrieveProjectsException(KeystoneAuthException):
    """Unable to retrieve authorized projects."""


class KeystoneRetrieveDomainsException(KeystoneAuthException):
    """Unable to retrieve authorized domains."""


class KeystoneConnectionException(KeystoneAuthException):
    """Unable to establish connection to keystone endpoint."""


class KeystoneCredentialsException(KeystoneAuthException):
    """Invalid credentials."""


class KeystonePassExpiredException(KeystoneAuthException):
    """The password is expired and needs to be changed."""
