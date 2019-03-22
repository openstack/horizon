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
# https://docs.openstack.org/horizon/latest/contributor/topics/
# microversion_support.html
MICROVERSION_FEATURES = {
    "nova": {
        "locked_attribute": ["2.9", "2.42"],
        "instance_description": ["2.19", "2.42"],
        "remote_console_mks": ["2.8", "2.53"],
        "servergroup_soft_policies": ["2.15", "2.60"],
        "servergroup_user_info": ["2.13", "2.60"],
        "multiattach": ["2.60"],
        "auto_allocated_network": ["2.37", "2.42"],
        "key_types": ["2.2", "2.9"],
        "key_type_list": ["2.9"],
    },
    "cinder": {
        "groups": ["3.27", "3.43", "3.48", "3.58"],
        "message_list": ["3.5", "3.29"],
        "limits_project_id_query": ["3.43", "3.50", "3.55"],
    }
}


class MicroVersionNotFound(Exception):
    def __init__(self, features):
        self.features = features

    def __str__(self):
        return "Insufficient microversion for %s" % self.features


def get_requested_versions(service, features):
    if not features:
        return None
    # Convert a single feature string into a list for backward compatibility.
    if isinstance(features, str):
        features = [features]
    try:
        service_features = MICROVERSION_FEATURES[service]
    except KeyError:
        LOG.debug("'%s' could not be found in the MICROVERSION_FEATURES dict",
                  service)
        return None

    feature_versions = set(service_features[features[0]])
    for feature in features[1:]:
        feature_versions &= set(service_features[feature])
    if not feature_versions:
        return None
    # Sort version candidates from larger versins
    feature_versions = sorted(feature_versions, reverse=True,
                              key=lambda v: [int(i) for i in v.split('.')])
    return feature_versions


# NOTE(robcresswell): Since each client implements their own wrapper class for
# API objects, we'll need to allow that to be passed in. In the future this
# should be replaced by some common handling in Oslo.
def get_microversion_for_features(service, features, wrapper_class,
                                  min_ver, max_ver):
    """Retrieves that highest known functional microversion for features"""
    feature_versions = get_requested_versions(service, features)
    if not feature_versions:
        return None

    for version in feature_versions:
        microversion = wrapper_class(version)
        if microversion.matches(min_ver, max_ver):
            return microversion
    return None
