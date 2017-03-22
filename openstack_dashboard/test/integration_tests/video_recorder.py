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
import signal
import subprocess
from tempfile import mktemp
from threading import Thread
import time

LOG = logging.getLogger(__name__)


class VideoRecorder(object):

    def __init__(self, width, height, display='0.0', frame_rate=15):
        self.is_launched = False
        self.file_path = mktemp() + '.mp4'
        # avconv -f x11grab -r 15 -s 1920x1080 -i :0.0 -codec libx264 out.mp4
        self._cmd = ['avconv', '-f', 'x11grab', '-r', str(frame_rate),
                     '-s', '{}x{}'.format(width, height),
                     '-i', ':{}'.format(display),
                     '-codec', 'libx264', self.file_path]

    def start(self):
        if self.is_launched:
            LOG.warning('Video recording is running already')
            return

        if not os.environ.get('AVCONV_INSTALLED', False):
            LOG.error("avconv isn't installed. Video recording is skipped")
            return

        fnull = open(os.devnull, 'w')
        LOG.info('Record video via %s', ' '.join(self._cmd))
        self._popen = subprocess.Popen(self._cmd, stdout=fnull, stderr=fnull)
        self.is_launched = True

    def stop(self):
        if not self.is_launched:
            LOG.warning('Video recording is stopped already')
            return

        self._popen.send_signal(signal.SIGINT)

        def terminate_avconv():
            limit = time.time() + 10

            while time.time() < limit:
                time.sleep(0.1)
                if self._popen.poll() is not None:
                    return

            os.kill(self._popen.pid, signal.SIGTERM)

        t = Thread(target=terminate_avconv)
        t.start()

        self._popen.communicate()
        t.join()
        self.is_launched = False

    def clear(self):
        if self.is_launched:
            LOG.error("Video recording is running still")
            return

        if not os.path.isfile(self.file_path):
            LOG.warning("%s is absent already", self.file_path)
            return

        os.remove(self.file_path)
