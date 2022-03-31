==========================
Releasing Horizon Projects
==========================

Since the responsibility for releases will move between people, we document
that process here.

A full list of projects that horizon manages is available in the
`governance site <https://governance.openstack.org/reference/projects/horizon.html>`__.

Who is responsible for releases?
--------------------------------

The current PTL is ultimately responsible for making sure code gets released.
They may choose to delegate this responsibility to a liaison, which is
documented in the `cross-project liaison wiki
<https://wiki.openstack.org/wiki/CrossProjectLiaisons#Release_management>`__.

Anyone may submit a release request per the process below, but the PTL or
liaison must +1 the request for it to be processed.

Release process
---------------

Releases are managed by the OpenStack release team. The release process is
documented in the `Project Team Guide
<https://docs.openstack.org/project-team-guide/release-management.html#how-to-release>`__.

In general, horizon deliverables follow the `cycle-with-intermediary
<https://releases.openstack.org/reference/release_models.html#cycle-with-intermediary>`__
release model.

Things to do before releasing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Update default policy-in-code rules in horizon for all backend services
  like cinder/glance/keystone/neutron/nova. For more information on how to
  update these policy rules see the :doc:`/contributor/topics/policy`.
* Check for any open patches that are close to be merged or release critical.
  This usually includes important bug fixes and/or features that we'd
  like to release, including the related documentation.
