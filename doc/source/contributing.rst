==================
Contributing Guide
==================

First and foremost, thank you for wanting to contribute! It's the only way
open source works!

Before you dive into writing patches, here are some of the basics:

* Project page: http://launchpad.net/horizon
* Bug tracker: https://bugs.launchpad.net/horizon
* Source code: https://github.com/openstack/horizon
* Code review: https://review.openstack.org/#q,status:open+project:openstack/horizon,n,z
* Continuous integration:

  * Jenkins: https://jenkins.openstack.org
  * Zuul: http://status.openstack.org/zuul
* IRC Channel: #openstack-horizon on Freenode.

Making Contributions
====================

Getting Started
---------------

We'll start by assuming you've got a working checkout of the repository (if
not then please see the :doc:`quickstart`).

Second, you'll need to take care of a couple administrative tasks:

#. Create an account on Launchpad.
#. Sign the `OpenStack Contributor License Agreement`_ and follow the associated
   instructions to verify your signature.
#. Join the `Horizon Developers`_ team on Launchpad.
#. Follow the `instructions for setting up git-review`_ in your
   development environment.

Whew! Got that all that? Okay! You're good to go.

Ways To Contribute
------------------

The easiest way to get started with Horizon's code is to pick a bug on
Launchpad that interests you, and start working on that. Alternatively, if
there's an OpenStack API feature you would like to see implemented in Horizon
feel free to try building it.

If those are too big, there are lots of great ways to get involved without
plunging in head-first:

* Report bugs, triage new tickets, and review old tickets on
  the `bug tracker`_.
* Propose ideas for improvements via `Launchpad Blueprints`_, via the
  mailing list on the project page, or on IRC.
* Write documentation!
* Write unit tests for untested code!

.. _`bug tracker`: https://bugs.launchpad.net/horizon
.. _`Launchpad Blueprints`: https://blueprints.launchpad.net/horizon

Choosing Issues To Work On
--------------------------

In general, if you want to write code, there are three cases for issues
you might want to work on:

#. Confirmed bugs
#. Approved blueprints (features)
#. New bugs you've discovered

If you have an idea for a new feature that isn't in a blueprint yet, it's
a good idea to write the blueprint first so you don't end up writing a bunch
of code that may not go in the direction the community wants.

For bugs, open the bug first, but if you can reproduce the bug reliably and
identify its cause then it's usually safe to start working on it. However,
getting independent confirmation (and verifying that it's not a duplicate)
is always a good idea if you can be patient.

After You Write Your Patch
--------------------------

Once you've made your changes, there are a few things to do:

* Make sure the unit tests pass: ``./run_tests.sh``
* Make sure PEP8 is clean: ``./run_tests.sh --pep8``
* Make sure your code is up-to-date with the latest master: ``git pull --rebase``
* Finally, run ``git review`` to upload your changes to Gerrit for review.

The Horizon core developers will be notified of the new review and will examine
it in a timely fashion, either offering feedback or approving it to be merged.
If the review is approved, it is sent to Jenkins to verify the unit tests pass
and it can be merged cleanly. Once Jenkins approves it, the change will be
merged to the master repository and it's time to celebrate!

.. _`OpenStack Contributor License Agreement`: http://wiki.openstack.org/CLA
.. _`OpenStack Contributors`: https://launchpad.net/~openstack-cla
.. _`Horizon Developers`: https://launchpad.net/~horizon
.. _`instructions for setting up git-review`: http://wiki.openstack.org/GerritWorkflow

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

Code Style
==========

Python
------

We follow PEP8_ for all our Python code, and use ``pep8.py`` (available
via the shortcut ``./run_tests.sh --pep8``) to validate that our code
meets proper Python style guidelines.

.. _PEP8: http://www.python.org/dev/peps/pep-0008/

Django
------

Additionally, we follow `Django's style guide`_ for templates, views, and
other miscellany.

.. _Django's style guide: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

JavaScript
----------

As a project, Horizon adheres to code quality standards for our JavaScript
just as we do for our Python. To that end we recommend (but do not strictly
enforce) the use of JSLint_ to validate some general best practices.

The default options are mostly good, but the following accommodate some
allowances we make:

* Set ``Indentation`` to ``2``.
* Enable the ``Assume console, alert, ...`` option.
* Enable the ``Assume a browser`` option.
* Enable the ``Tolerate missing 'use strict' pragma`` option.
* Clear the ``Maximum number of errors`` field.
* Add ``horizon,$`` to the ``Predefined`` list.

We don't require that everything works with JavaScript disabled. It's fine to
introduce features that require that JavaScript is enabled in the user's web
browser.

The code has to work on the stable and latest versions of Firefox, Chrome,
Safari, and Opera web browsers, and on Microsoft Internet Explorer 9 and later.

.. _JSLint: http://jslint.com/

CSS
---

Style guidelines for CSS are currently quite minimal. Do your best to make the
code readable and well-organized. Two spaces are preferred for indentation
so as to match both the JavaScript and HTML files.


JavaScript and CSS libraries
----------------------------

We do not bundle the third-party code within Horizon's source tree anymore, any
code that is still there is just left over and will be cleaned up and packaged
properly eventually. What we do instead, is packaging the required files as
XStatic Python packages and adding them as dependencies to Horizon. In
particular, when you need to add a new third-party JavaScript or CSS library to
Horizon, follow those steps:

 1. Check if the library is already packaged as Xstatic on PyPi, by searching
    for the library name. If it already is, go to step 5. If it is, but not in
    the right version, contact the original packager.
 2. Package the library as an Xstatic package by following the instructions in
    Xstatic documentation_.
 3. Register and upload your library to PyPi. Add "openstackci" user as an
    owner of that package. Don't forget to tag your release in the repository.
 4. Create a new repository on StackForge_. Use "xstatic-core" and
    "xstatic-ptl" groups for the ACLs.
 5. Add the package to global-requirements_. Make sure to mention the license.
 6. Add the package to Horizon's ``requirements.txt`` file, to its
    ``settings.py``, and to the ``_scripts.html`` or ``_stylesheets.html``
    templates. Make sure to keep the order alphabetic.

.. _documentation: http://xstatic.rtfd.org/en/latest/packaging.html
.. _StackForge: http://ci.openstack.org/stackforge.html#add-a-project-to-stackforge
.. _global-requirements: https://github.com/openstack/requirements/blob/master/global-requirements.txt


HTML
----

Again, readability is paramount; however be conscientious of how the browser
will handle whitespace when rendering the output. Two spaces is the preferred
indentation style to match all front-end code.

Documentation
-------------

Horizon's documentation is written in reStructuredText and uses Sphinx for
additional parsing and functionality, and should follow
standard practices for writing reST. This includes:

* Flow paragraphs such that lines wrap at 80 characters or less.
* Use proper grammar, spelling, capitalization and punctuation at all times.
* Make use of Sphinx's autodoc feature to document modules, classes
  and functions. This keeps the docs close to the source.
* Where possible, use Sphinx's cross-reference syntax (e.g.
  ``:class:`~horizon.foo.Bar```) when referring to other Horizon components.
  The better-linked our docs are, the easier they are to use.

Be sure to generate the documentation before submitting a patch for review.
Unexpected warnings often appear when building the documentation, and slight
reST syntax errors frequently cause links or cross-references not to work
correctly.

Conventions
-----------

Simply by convention, we have a few rules about naming:

  * The term "project" is used in place of Keystone's "tenant" terminology
    in all user-facing text. The term "tenant" is still used in API code to
    make things more obvious for developers.

  * The term "dashboard" refers to a top-level dashboard class, and "panel" to
    the sub-items within a dashboard. Referring to a panel as a dashboard is
    both confusing and incorrect.
