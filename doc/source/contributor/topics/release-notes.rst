=============
Release Notes
=============

Release notes for a patch should be included in the patch with the
associated changes whenever possible. This allow for simpler tracking. It also
enables a single cherry pick to be done if the change is backported to a
previous release. In some cases, such as a feature that is provided via
multiple patches, release notes can be done in a follow-on review.

If the following applies to the patch, a release note is required:

* The deployer needs to take an action when upgrading
* A new feature is implemented
* Function was removed (hopefully it was deprecated)
* Current behavior is changed
* A new config option is added that the deployer should consider changing from
  the default
* A security bug is fixed

.. note::

   * A release note is suggested if a long-standing or important bug is fixed.
     Otherwise, a release note is not required.
   * It is not recommended that individual release notes use **prelude**
     section as it is for release highlights.

.. warning::

   Avoid modifying an existing release note file even though it is related to
   your change. If you modify a release note file of a past release, the whole
   content will be shown in a latest release. The only allowed case is to
   update a release note in a same release.

   If you need to update a release note of a past release, edit a corresponding
   release note file in a stable branch directly.

Horizon uses `reno <https://docs.openstack.org/reno/latest/user/usage.html>`_ to
generate release notes. Please read the docs for details. In summary, use

.. code-block:: bash

  $ tox -e venv -- reno new <bug-,bp-,whatever>

Then edit the sample file that was created and push it with your change.

To see the results:

.. code-block:: bash

  $ git commit  # Commit the change because reno scans git log.

  $ tox -e releasenotes

Then look at the generated release notes files in releasenotes/build/html in
your favorite browser.
