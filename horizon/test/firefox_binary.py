# Copyright 2015, Rackspace, US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import platform
import shutil
import subprocess

from selenium.common import exceptions as selenium_exceptions
from selenium.webdriver.common import desired_capabilities as dc
from selenium.webdriver import firefox


class FirefoxBinary(firefox.firefox_binary.FirefoxBinary):
    """Workarounds selenium firefox issues.

    There is race condition in the way firefox is spawned. The exact
    cause hasn't been properly diagnosed yet but it's around:

    - getting a free port from the OS with
    selenium.webdriver.common.utils free_port(),

    - release the port immediately but record it in ff prefs so that ff
    can listen on that port for the internal http server.

    It has been observed that this leads to hanging processes for
    'firefox -silent'.
    """

    def _start_from_profile_path(self, path):
        self._firefox_env["XRE_PROFILE_PATH"] = path

        if platform.system().lower() == 'linux':
            self._modify_link_library_path()
        command = [self._start_cmd, "-silent"]
        if self.command_line is not None:
            for cli in self.command_line:
                command.append(cli)

# The following exists upstream and is known to create hanging
# firefoxes, leading to zombies.
#        subprocess.Popen(command, stdout=self._log_file,
#              stderr=subprocess.STDOUT,
#              env=self._firefox_env).communicate()
        command[1] = '-foreground'
        self.process = subprocess.Popen(
            command, stdout=self._log_file, stderr=subprocess.STDOUT,
            env=self._firefox_env)


class WebDriver(firefox.webdriver.WebDriver):
    """Workarounds selenium firefox issues."""
    def __init__(self, firefox_profile=None, firefox_binary=None, timeout=30,
                 desired_capabilities=dc.DesiredCapabilities.FIREFOX,
                 proxy=None):
        try:
            super(WebDriver, self).__init__(
                firefox_profile, FirefoxBinary(), timeout,
                desired_capabilities, proxy)
        except selenium_exceptions.WebDriverException:
            # If we can't start, cleanup profile
            shutil.rmtree(self.profile.path)
            if self.profile.tempfolder is not None:
                shutil.rmtree(self.profile.tempfolder)
            raise
