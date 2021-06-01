============================
So You Want to Contribute...
============================

For general information on contributing to OpenStack, please check out the
`contributor guide <https://docs.openstack.org/contributors/>`_ to get started.
It covers all the basics that are common to all OpenStack projects: the accounts
you need, the basics of interacting with our Gerrit review system, how we
communicate as a community, etc.

Below will cover the more project specific information you need to get started
with horizon.

Project Resources
-----------------

* Source code: https://opendev.org/openstack/horizon
* Documentation: https://docs.openstack.org/horizon/latest/
* Project page: https://launchpad.net/horizon
* Bug tracker: https://bugs.launchpad.net/horizon
* Code review: https://review.opendev.org/#/q/project:openstack/horizon+status:open

Communication
-------------

* IRC channel: ``#openstack-horizon`` at OFTC

  Most active contributors are online at IRC while they are active,
  so it would be the easiest way to contact the team directly.
  Note that all IRC conversations are stored
  `here <http://eavesdrop.openstack.org/irclogs/%23openstack-horizon/>`__.

* Mailing list:
  `openstack-discuss
  <http://lists.openstack.org/cgi-bin/mailman/listinfo/openstack-discuss>`__
  with ``[horizon]`` tag.

  The mailing list would be a good place if you would like to discuss your
  topic with the OpenStack community more broadly. Most OpenStack users,
  operators and developers subscribe it and you can get useful feedbacks
  from various perspectives.

* Team meeting:

  The horizon team has a weekly meeting which covers all things related to
  the horizon project like announcements, project priorities, community goals,
  bugs and so on.

  There is the "On Demand Agenda" section at the end of the meeting, where
  anyone can add a topic to discuss with the team. It is suggested to add
  such topic to the On-Demand agenda in the "Weekly meeting" in
  `horizon release priority etherpad
  <https://etherpad.opendev.org/p/horizon-release-priorities>`__.

  * Time: http://eavesdrop.openstack.org/#Horizon_Team_Meeting
  * Agenda: https://wiki.openstack.org/wiki/Meetings/Horizon

Contacting the Core Team
------------------------

The list of the current core reviewers is found at
`gerrit <https://review.opendev.org/#/admin/groups/43,members>`__.

Most core reviewers are online in the IRC channel and
you can contact them there.

New Feature Planning
--------------------

If you would like to add a new feature to horizon, file a blueprint
to https://blueprints.launchpad.net/horizon. You can find a template for a
blueprint at https://blueprints.launchpad.net/horizon/+spec/template.
The template is not a strict requirement but it would be nice to cover
a motivation and an approach of your blueprint. From the nature of GUI,
a discussion on UI design during a patch review could be more productive,
so there is no need to explain the detail of UI design in your blueprint
proposal.

We don't have a specific deadline during a development cycle. You can propose a
feature any time. Only thing you keep in your mind is that we do not merge
features during the feature freeze period after the milestone 3 in each cycle.

There are a number of unsupported OpenStack features in horizon.
Implementing such would be appreciated even if it is small.

Task Tracking
-------------

We track our tasks in `Launchpad <https://bugs.launchpad.net/horizon>`__.

If you're looking for some smaller, please look through the list of bugs
and find what you think you can work on. If you are not sure the status of
a bug feel free to ask to the horizon team. We can help you.
Note that we recently do not maintain 'low-hanging-fruit' tag and some of
them with this tag are not simple enough.

Reporting a Bug
---------------

You found an issue and want to make sure we are aware of it?
You can do so on `Launchpad <https://bugs.launchpad.net/horizon>`__.

Please file a bug first even if you already have a fix for it.
If you can reproduce the bug reliably and identify its cause
then it's usually safe to start working on it.
However, getting independent confirmation (and verifying that it's not a
duplicate) is always a good idea if you can be patient.

Getting Your Patch Merged
-------------------------

All changes proposed to horizon require two +2 votes from the horizon core
reviewers before one of the core reviewers can approve a change by giving
"Workflow +1" vote.

In general, all changes should be proposed along with at least unit test
coverage (python or JavaScript). Integration test support would be
appreciated.

More detailed guidelines for reviewers of patches are available at
`OpenDev Developer's Guide <https://docs.opendev.org/opendev/infra-manual/latest/developers.html#code-review>`__.

Project Team Lead Duties
------------------------

All common PTL duties are enumerated in the `PTL guide
<https://docs.openstack.org/project-team-guide/ptl.html>`_.

The horizon PTL is expected to coordinate and encourage the core reviewer team
and contributors for the success. The expectations for the core reviewer team
is documented at :doc:`policies/core-reviewers` and the PTL would play an
important role in this.

Etiquette
---------

The community's guidelines for etiquette are fairly simple:

* Treat everyone respectfully and professionally.
* If a bug is "in progress" in the bug tracker, don't start working on it
  without contacting the author. Try on IRC, or via the launchpad email
  contact link. If you don't get a response after a reasonable time, then go
  ahead. Checking first avoids duplicate work and makes sure nobody's toes
  get stepped on.
* If a blueprint is assigned, even if it hasn't been started, be sure you
  contact the assignee before taking it on. These larger issues often have a
  history of discussion or specific implementation details that the assignee
  may be aware of that you are not.
* Please don't re-open tickets closed by a core developer. If you disagree with
  the decision on the ticket, the appropriate solution is to take it up on
  IRC or the mailing list.
* Give credit where credit is due; if someone helps you substantially with
  a piece of code, it's polite (though not required) to thank them in your
  commit message.
