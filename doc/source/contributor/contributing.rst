==================
Contributing Guide
==================

First and foremost, thank you for wanting to contribute! It's the only way
open source works!

Before you dive into writing patches, here are some of the basics:

* Project page: https://launchpad.net/horizon
* Bug tracker: https://bugs.launchpad.net/horizon
* Source code: https://github.com/openstack/horizon
* Code review: https://review.opendev.org/#/q/project:openstack/horizon+status:open
* Continuous integration:
  * Jenkins: https://jenkins.openstack.org
  * Zuul: http://status.openstack.org/zuul
* IRC Channel: #openstack-horizon on Freenode.

Making Contributions
====================

Getting Started
---------------

We'll start by assuming you've got a working checkout of the repository (if
not then please see the :ref:`quickstart`).

Second, you'll need to take care of a couple administrative tasks:

#. Create an account on Launchpad.
#. Sign the `OpenStack Contributor License Agreement`_ and follow the associated
   instructions to verify your signature.
#. Join the `Horizon Developers`_ team on Launchpad.
#. Follow the `instructions for setting up git-review`_ in your
   development environment.

Whew! Got all that? Okay! You're good to go.

.. _`OpenStack Contributor License Agreement`: https://wiki.openstack.org/CLA
.. _`Horizon Developers`: https://launchpad.net/~horizon
.. _`instructions for setting up git-review`: https://docs.openstack.org/infra/manual/developers.html#development-workflow

Ways To Contribute
------------------

The easiest way to get started with Horizon's code is to pick a bug on
Launchpad that interests you, and start working on that. Bugs tagged as
``low-hanging-fruit`` are a good place to start. Alternatively, if there's an
OpenStack API feature you would like to see implemented in Horizon feel free
to try building it.

If those are too big, there are lots of great ways to get involved without
plunging in head-first:

* Report bugs, triage new tickets, and review old tickets on
  the `bug tracker`_.
* Propose ideas for improvements via `Launchpad Blueprints`_, via the
  mailing list on the project page, or on IRC.
* Write documentation!
* Write unit tests for untested code!
* Help improve the `User Experience Design`_ or contribute to the
  `Persona Working Group`_.

.. _`bug tracker`: https://bugs.launchpad.net/horizon
.. _`Launchpad Blueprints`: https://blueprints.launchpad.net/horizon
.. _`User Experience Design`: https://wiki.openstack.org/wiki/UX#Getting_Started
.. _`Persona Working Group`: https://wiki.openstack.org/wiki/Personas

Choosing Issues To Work On
--------------------------

In general, if you want to write code, there are three cases for issues
you might want to work on:

#. Confirmed bugs
#. Approved blueprints (features)
#. New bugs you've discovered

If you have an idea for a new feature that isn't in a blueprint yet, it's
a good idea to write the blueprint first, so you don't end up writing a bunch
of code that may not go in the direction the community wants.

For bugs, open the bug first, but if you can reproduce the bug reliably and
identify its cause then it's usually safe to start working on it. However,
getting independent confirmation (and verifying that it's not a duplicate)
is always a good idea if you can be patient.

After You Write Your Patch
--------------------------

Once you've made your changes, there are a few things to do:

* Make sure the unit tests and linting tasks pass by running ``tox``
* Take a look at your patch in API profiler, i.e. how it impacts the
  performance. See :doc:`topics/profiling`.
* Make sure your code is ready for translation: See :ref:`pseudo_translation`.
* Make sure your code is up-to-date with the latest master:
  ``git pull --rebase``
* Finally, run ``git review`` to upload your changes to Gerrit for review.

The Horizon core developers will be notified of the new review and will examine
it in a timely fashion, either offering feedback or approving it to be merged.
If the review is approved, it is sent to Jenkins to verify the unit tests pass
and it can be merged cleanly. Once Jenkins approves it, the change will be
merged to the master repository and it's time to celebrate!

Etiquette
=========

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
