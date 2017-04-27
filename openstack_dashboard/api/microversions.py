# Copyright 2017 Cisco Systems
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging

LOG = logging.getLogger(__name__)

# A list of features and their supported microversions. Note that these are
# explicit functioning versions, not a range.
# There should be a minimum of two versions per feature. The first entry in
# this list should always be the lowest possible API microversion for a
# feature i.e. the version at which that feature was introduced. The second
# entry should be the current service version when the feature was added to
# horizon.
# Further documentation can be found at
# http://docs.openstack.org/developer/horizon/topics/microversion_support.html
MICROVERSION_FEATURES = {
    "nova": {
        "locked_attribute": ["2.9", "2.42"]
    },
    "cinder": {
        "consistency_groups": ["2.0", "3.10"],
        "message_list": ["3.5", "3.29"]
    }
}


# NOTE(robcresswell): Since each client implements their own wrapper class for
# API objects, we'll need to allow that to be passed in. In the future this
# should be replaced by some common handling in Oslo.
def get_microversion_for_feature(service, feature, wrapper_class,
                                 min_ver, max_ver):
    """Retrieves that highest known functional microversion for a feature"""
    try:
        service_features = MICROVERSION_FEATURES[service]
    except KeyError:
        LOG.debug("'%s' could not be found in the MICROVERSION_FEATURES dict",
                  service)
        return None
    feature_versions = service_features[feature]
    for version in reversed(feature_versions):
        microversion = wrapper_class(version)
        if microversion.matches(min_ver, max_ver):
            return microversion
    return None
