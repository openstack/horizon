=============
Horizon Teams
=============

Horizon project defines several teams to maintain the project.

Gerrit
------

Core Reviewer Team
~~~~~~~~~~~~~~~~~~

The core reviewer team is responsible for the horizon development
in the master branch from various perspective.
See :doc:`core-reviewers` for more detail.

Stable Maintenance Team
~~~~~~~~~~~~~~~~~~~~~~~

Members of this gerrit group are responsible for maintaining
stable branches. The members are expected to understand
`the stable branch policy <https://docs.openstack.org/project-team-guide/stable-branches.html>`__.
Most members overlaps with the core reviewer team but being a core reviewer is
not a requirement for being a member of the stable maintenance team.
Folks who would like to be a member of this team is recommended to express how
they understand the stable branch policy in reviews.

The member list is found at
https://review.opendev.org/#/admin/groups/537,members.

Launchpad
---------

Bug Supervisor Team
~~~~~~~~~~~~~~~~~~~

Members of this launchpad group are responsible for bug management.
They have privileges to set status, priority and milestone of bugs.
Most members overlaps with the core reviewer team
but it is not a requirement for being a member of this team.

The member list is found at https://launchpad.net/~horizon-bugs.

Horizon Drivers Team
~~~~~~~~~~~~~~~~~~~~

Members of this launchpad group can do all things in the horizon launchpad
such as defining series and milestones. This group is included to the bug
supervisor team.

The member list is found at https://launchpad.net/~horizon-drivers.

Security Contact Team
~~~~~~~~~~~~~~~~~~~~~

Members of this launchpad group are responsible for security issues.
Members are expected to be familiar with
`Vulnerability Management Process
<https://security.openstack.org/vmt-process.html>`__ in OpenStack.
Private security issues are handled differently from usual public reports.
All steps including patch development and review are done in a launchpad
bug report.

The member list is found at https://launchpad.net/~horizon-coresec.

Note that the access permission to private information of this team
is configured at https://launchpad.net/horizon/+sharing. (You can find
"Sharing" menu at the top-right corder of `the launchpad top page
<https://launchpad.net/horizon>`__.)
