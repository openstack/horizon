# (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.conf import settings

from django_pyscss.compressor import DjangoScssFilter
from django_pyscss import DjangoScssCompiler

from scss.namespace import Namespace
from scss.types import String


class HorizonScssFilter(DjangoScssFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.namespace = Namespace()

        # Add variables to the SCSS Global Namespace Here
        self.namespace.set_variable(
            '$static_url',
            String(settings.STATIC_URL)
        )

    # Create a compiler with the right namespace
    @property
    def compiler(self):
        return DjangoScssCompiler(
            # output_style is 'nested' by default, which is crazy. See:
            # https://github.com/Kronuz/pyScss/issues/243
            output_style='compact',  # or 'compressed'
            namespace=self.namespace
        )
