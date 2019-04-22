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
  performance. See `Profiling Pages`_.
* Make sure your code is ready for translation: See :ref:`pseudo_translation`.
* Make sure your code is up-to-date with the latest master:
  ``git pull --rebase``
* Finally, run ``git review`` to upload your changes to Gerrit for review.

The Horizon core developers will be notified of the new review and will examine
it in a timely fashion, either offering feedback or approving it to be merged.
If the review is approved, it is sent to Jenkins to verify the unit tests pass
and it can be merged cleanly. Once Jenkins approves it, the change will be
merged to the master repository and it's time to celebrate!

Profiling Pages
---------------

In the Ocata release of Horizon a new "OpenStack Profiler" panel was
introduced. Once it is enabled and all prerequisites are set up, you can see
which API calls Horizon actually makes when rendering a specific page. To
re-render the page while profiling it, you'll need to use the "Profile"
dropdown menu located in the top right corner of the screen. In order to
be able to use "Profile" menu, the following steps need to be completed:

#. Enable the Developer dashboard by copying ``_9001_developer.py`` from
   ``openstack_dashboard/contrib/developer/enabled/`` to
   ``openstack_dashboard/local/enabled/``.
#. Copy
   ``openstack_dashboard/local/local_settings.d/_9030_profiler_settings.py.example``
   to ``openstack_dashboard/local/local_settings.d/_9030_profiler_settings.py``
#. Copy ``openstack_dashboard/contrib/developer/enabled/_9030_profiler.py`` to
   ``openstack_dashboard/local/enabled/_9030_profiler.py``.
#. To support storing profiler data on server-side, MongoDB cluster needs to be
   installed on your Devstack host (default configuration), see
   `Installing MongoDB`_. Then, change the ``bindIp`` key in
   ``/etc/mongod.conf`` to ``0.0.0.0`` and invoke
   ``sudo service mongod restart``.
#. Collect and compress static assets with
   ``python manage.py collectstatic -c`` and ``python manage.py compress``
#. Restart the web server.
#. The "Profile" drop-down menu should appear in the top-right corner, you are
   ready to profile your pages!

.. _installing MongoDB: https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/#install-mongodb-community-edition

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

As a project, Horizon adheres to code quality standards.

Python
------

We follow PEP8_ for all our Python code, and use ``pep8.py`` (available
via the shortcut ``tox -e pep8``) to validate that our code
meets proper Python style guidelines.

.. _PEP8: https://www.python.org/dev/peps/pep-0008/

Django
------

Additionally, we follow `Django's style guide`_ for templates, views, and
other miscellany.

.. _Django's style guide: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

JavaScript
----------

The following standards are divided into required and recommended sections.
Our main goal in establishing these best practices is to have code that is
reliable, readable, and maintainable.

Required
~~~~~~~~

**Reliable**

* The code has to work on the stable and latest versions of Firefox, Chrome,
  Safari, and Opera web browsers, and on Microsoft Internet Explorer 11 and
  later.

* If you turned compression off during development via ``COMPRESS_ENABLED =
  False`` in local_settings.py, re-enable compression and test your code
  before submitting.

* Use ``===`` as opposed to ``==`` for equality checks. The ``==`` will do a
  type cast before comparing, which can lead to unwanted results.

  .. note::

     If typecasting is desired, explicit casting is preferred to keep the
     meaning of your code clear.

* Keep document reflows to a minimum. DOM manipulation is expensive, and can
  become a performance issue. If you are accessing the DOM, make sure that you
  are doing it in the most optimized way. One example is to build up a document
  fragment and then append the fragment to the DOM in one pass instead of doing
  multiple smaller DOM updates.

* Use "strict", enclosing each JavaScript file inside a self-executing
  function. The self-executing function keeps the strict scoped to the file,
  so its variables and methods are not exposed to other JavaScript files in
  the product.

  ..  Note ::
      Using strict will throw exceptions for common coding errors, like
      accessing global vars, that normally are not flagged.

  Example:
  ::

    (function(){
      'use strict';
      // code...
    })();

* Use ``forEach`` | ``each`` when looping whenever possible. AngularJS and
  jQuery both provide for each loops that provide both iteration and scope.

  AngularJS:
  ::

    angular.forEach(objectToIterateOver, function(value, key) {
      // loop logic
    });

  jQuery:
  ::

    $.each(objectToIterateOver, function(key, value) {
      // loop logic
    });

* Do not put variables or functions in the global namespace. There are several
  reasons why globals are bad, one being that all JavaScript included in an
  application runs in the same scope. The issue with that is if another script
  has the same method or variable names they overwrite each other.
* Always put ``var`` in front of your variables. Not putting ``var`` in front
  of a variable puts that variable into the global space, see above.
* Do not use ``eval( )``. The eval (expression) evaluates the expression
  passed to it. This can open up your code to security vulnerabilities and
  other issues.
* Do not use '``with`` object {code}'. The ``with`` statement is used to access
  properties of an object. The issue with ``with`` is that its execution is not
  consistent, so by reading the statement in the code it is not always clear
  how it is being used.

**Readable & Maintainable**

* Give meaningful names to methods and variables.
* Avoid excessive nesting.
* Avoid HTML and CSS in JS code. HTML and CSS belong in templates and
  stylesheets respectively. For example:

  * In our HTML files, we should focus on layout.

    1. Reduce the small/random ``<script>`` and ``<style>`` elements in HTML.

    2. Avoid in-lining styles into element in HTML. Use attributes and
       classes instead.

  * In our JS files, we should focus on logic rather than attempting to
    manipulate/style elements.

    1. Avoid statements such as ``element.css({property1,property2...})`` they
       belong in a CSS class.

    2. Avoid statements such as ``$("<div><span>abc</span></div>")`` they
       belong in a HTML template file. Use ``show`` | ``hide`` | ``clone``
       elements if dynamic content is required.

    3. Avoid using classes for detection purposes only, instead, defer to
       attributes. For example to find a div:

       .. code-block:: html

          <div class="something"></div>
            $(".something").html("Don't find me this way!");

       is better found like:

       .. code-block:: html

          <div data-something></div>
            $("div[data-something]").html("You found me correctly!");

* Avoid commented-out code.
* Avoid dead code.

**Performance**

* Avoid creating instances of the same object repeatedly within the same scope.
  Instead, assign the object to a variable and re-use the existing object. For
  example:
  ::

     $(document).on('click', function() { /* do something. */ });
     $(document).on('mouseover', function() { /* do something. */ });

  A better approach:
  ::

     var $document = $(document);
     $document.on('click', function() { /* do something. */ });
     $document.on('mouseover', function() { /* do something. */ });

  In the first approach a jQuery object for ``document`` is created each time.
  The second approach creates only one jQuery object and reuses it. Each object
  needs to be created, uses memory, and needs to be garbage collected.

Recommended
~~~~~~~~~~~

**Readable & Maintainable**

* Put a comment at the top of every file explaining what the purpose of this
  file is when the naming is not obvious. This guideline also applies to
  methods and variables.
* Source-code formatting – (or "beautification") is recommended but should be
  used with caution. Keep in mind that if you reformat an entire file that was
  not previously formatted the same way, it will mess up the diff during the
  code review. It is best to use a formatter when you are working on a new file
  by yourself, or with others who are using the same formatter. You can also
  choose to format a selected portion of a file only. Instructions for setting
  up ESLint for Eclipse, Sublime Text, Notepad++ and WebStorm/PyCharm are
  provided_.
* Use 2 spaces for code indentation.
* Use ``{ }`` for ``if``, ``for``, ``while`` statements, and don't combine them
  on one line.
  ::

    // Do this          //Not this          // Not this
    if(x) {             if(x)               if(x) y =x;
      y=x;                y=x;
    }

* Use ESLint in your development environment.

.. _provided: https://wiki.openstack.org/wiki/Horizon/Javascript/EditorConfig

AngularJS
---------

.. Note::

  This section is intended as a quick intro to contributing with AngularJS. For
  more detailed information, check the :ref:`topics-angularjs`.

"John Papa Style Guide"
~~~~~~~~~~~~~~~~~~~~~~~

The John Papa Style Guide is the primary point of reference for Angular
code style. This style guide has been endorsed by the AngularJS
team::

 "The most current and detailed Angular Style Guide is the
 community-driven effort led by John Papa and Todd Motto."

 - http://angularjs.blogspot.com/2014/02/an-angularjs-style-guide-and-best.html

The style guide is found at the below location:

https://github.com/johnpapa/angular-styleguide

When reviewing / writing, please refer to the sections of this guide.
If an issue is encountered, note it with a comment and provide a link back
to the specific issue. For example, code should use named functions. A
review noting this should provide the following link in the comments:

https://github.com/johnpapa/angular-styleguide#style-y024

In addition to John Papa, the following guidelines are divided into
required and recommended sections.

Required
~~~~~~~~

* Scope is not the model (model is your JavaScript Objects). The scope
  references the model. Use isolate scopes wherever possible.

  * https://github.com/angular/angular.js/wiki/Understanding-Scopes
  * Read-only in templates.
  * Write-only in controllers.

* Since Django already uses ``{{ }}``, use ``{$ $}`` or ``{% verbatim %}``
  instead.

ESLint
------

ESLint is a great tool to be used during your code editing to improve
JavaScript quality by checking your code against a configurable list of checks.
Therefore, JavaScript developers should configure their editors to use ESLint
to warn them of any such errors so they can be addressed. Since ESLint has a
ton of configuration options to choose from, links are provided below to the
options Horizon wants enforced along with the instructions for setting up
ESLint for Eclipse, Sublime Text, Notepad++ and WebStorm/PyCharm.

Instructions for setting up ESLint: `ESLint setup instructions`_

..  Note ::
    ESLint is part of the automated unit tests performed by Jenkins. The
    automated test use the default configurations, which are less strict than
    the configurations we recommended to run in your local development
    environment.

.. _ESLint setup instructions: https://wiki.openstack.org/wiki/Horizon/Javascript/EditorConfig

CSS
---

Style guidelines for CSS are currently quite minimal. Do your best to make the
code readable and well-organized. Two spaces are preferred for indentation
so as to match both the JavaScript and HTML files.

JavaScript and CSS libraries using xstatic
------------------------------------------

We do not bundle third-party code in Horizon's source tree. Instead, we package
the required files as xstatic Python packages and add them as dependencies to
Horizon.

To create a new xstatic package:

1. Check if the library is already packaged as xstatic on PyPi, by searching
   for the library name. If it already is, go to step 5. If it is, but not in
   the right version, contact the original packager to have them update it.
2. Package the library as an xstatic package by following the instructions in
   xstatic documentation_. Install the xstatic-release_ script and follow
   the instructions that come with it.
3. `Create a new repository under OpenStack`_. Use "xstatic-core" and
   "xstatic-ptl" groups for the ACLs. Make sure to include the
   ``-pypi-wheel-upload`` job in the project config.
4. `Set up PyPi`_ to allow OpenStack (the "openstackci" user) to publish your
   package.
5. Add the new package to `global-requirements`_.

To make a new release of the package, you need to:

1. Ensure the version information in the
   `xstatic/pkg/<package name>/__init__.py` file is up to date,
   especially the `BUILD`.
2. Push your updated package up for review in gerrit.
3. Once the review is approved and the change merged, `request a release`_ by
   updating or creating the appropriate file for the xstatic package
   in the `releases repository`_ under `deliverables/_independent`. That
   will cause it to be automatically packaged and released to PyPi.

.. warning::

    Note that once a package is released, you can not "un-release" it. You
    should never attempt to modify, delete or rename a released package without
    a lot of careful planning and feedback from all projects that use it.

    For the purpose of fixing packaging mistakes, xstatic has the build number
    mechanism. Simply fix the error, increment the build number and release the
    newer package.

.. _documentation: https://xstatic.readthedocs.io/en/latest/packaging.html
.. _xstatic-release: https://pypi.org/project/xstatic-release/
.. _`Create a new repository under OpenStack`: https://docs.openstack.org/infra/manual/creators.html
.. _`request a release`: https://opendev.org/openstack/releases/src/branch/master/README.rst
.. _`releases repository`: https://opendev.org/openstack/releases
.. _`Set up PyPi`: https://docs.openstack.org/infra/manual/creators.html#give-openstack-permission-to-publish-releases
.. _global-requirements: https://github.com/openstack/requirements/blob/master/global-requirements.txt


Integrating a new xstatic package into Horizon
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Having done a release of an xstatic package:

1. Look for the `upper-constraints.txt`_ edit related to the xstatic release
   that was just performed. One will be created automatically by the release
   process in the ``openstack/requirements`` project with the topic
   `new-release`_. You should -1 that patch until you are confident Horizon
   does not break (or you have generated a patch to fix Horizon for that
   release.) If no upper-constraints.txt patch is automatically generated,
   ensure the releases yaml file created in the `releases repository`_ has the
   "include-pypi-link: yes" setting.
2. Pull that patch down so you have the edited upper-constraints.txt file
   locally.
3. Set the environment variable `UPPER_CONSTRAINTS_FILE` to the edited
   upper-constraints.txt file name and run tests or local development server
   through tox. This will pull in the precise version of the xstatic package
   that you need.
4. Move on to releasing once you're happy the Horizon changes are stable.

Releasing a new compatible version of Horizon to address issues in the new
xstatic release:

1. Continue to -1 the upper-constraints.txt patch above until this process is
   complete. A +1 from a Horizon developer will indicate to the requirements
   team that the upper-constraints.txt patch is OK to merge.
2. When submitting your changes to Horizon to address issues around the new
   xstatic release, use a Depends-On: referencing the upper-constraints.txt
   review. This will cause the OpenStack testing infrastructure to pull in your
   updated xstatic package as well.
3. Merge the upper-constraints.txt patch and the Horizon patch noting that
   Horizon's gate may be broken in the interim between these steps, so try to
   minimise any delay there. With the Depends-On it's actually safe to +W the
   Horizon patch, which will be held up until the related upper-constraints.txt
   patch merges.
4. Once the upper-constraints.txt patch merges, you should propose a patch to
   global-requirements which bumps the minimum version of the package up to the
   upper-constraints version so that deployers / packagers who don't honor
   upper-constraints still get compatible versions of the packages.

.. _upper-constraints.txt: https://opendev.org/openstack/requirements/raw/branch/master/upper-constraints.txt
.. _new-release: https://review.opendev.org/#/q/status:open+project:openstack/requirements+branch:master+topic:new-release


HTML
----

Again, readability is paramount; however be conscientious of how the browser
will handle whitespace when rendering the output. Two spaces is the preferred
indentation style to match all front-end code.

Exception Handling
------------------

Avoid propogating direct exception messages thrown by OpenStack APIs to the UI.
It is a precaution against giving obscure or possibly sensitive data to a user.
These error messages from the API are also not translatable. Until there is a
standard error handling framework implemented by the services which presents
clean and translated messages, horizon catches all the exceptions thrown by the
API and normalizes them in :func:`horizon.exceptions.handle`.


Documentation
-------------

Horizon's documentation is written in reStructuredText (reST) and uses Sphinx
for additional parsing and functionality, and should follow standard practices
for writing reST. This includes:

* Flow paragraphs such that lines wrap at 80 characters or less.
* Use proper grammar, spelling, capitalization and punctuation at all times.
* Make use of Sphinx's autodoc feature to document modules, classes
  and functions. This keeps the docs close to the source.
* Where possible, use Sphinx's cross-reference syntax (e.g.
  ``:class:`~horizon.foo.Bar``) when referring to other Horizon components.
  The better-linked our docs are, the easier they are to use.

Be sure to generate the documentation before submitting a patch for review.
Unexpected warnings often appear when building the documentation, and slight
reST syntax errors frequently cause links or cross-references not to work
correctly.

Documentation is generated with Sphinx using the tox command. To create HTML
docs and man pages:

.. code-block:: bash

    $ tox -e docs

The results are in the doc/build/html and doc/build/man directories
respectively.

Conventions
-----------

Simply by convention, we have a few rules about naming:

* The term "project" is used in place of Keystone's "tenant" terminology
  in all user-facing text. The term "tenant" is still used in API code to
  make things more obvious for developers.

* The term "dashboard" refers to a top-level dashboard class, and "panel" to
  the sub-items within a dashboard. Referring to a panel as a dashboard is
  both confusing and incorrect.

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

Core Reviewer Team
==================

The Horizon Core Reviewer Team is responsible for many aspects of the
Horizon project. These include, but are not limited to:

- Mentor community contributors in solution design, testing, and the
  review process
- Actively reviewing patch submissions, considering whether the patch:
  - is functional
  - fits the use-cases and vision of the project
  - is complete in terms of testing, documentation, and release notes
  - takes into consideration upgrade concerns from previous versions
- Assist in bug triage and delivery of bug fixes
- Curating the gate and triaging failures
- Maintaining accurate, complete, and relevant documentation
- Ensuring the level of testing is adequate and remains relevant as
  features are added
- Answering questions and participating in mailing list discussions
- Interfacing with other OpenStack teams

In essence, core reviewers share the following common ideals:

- They share responsibility in the project's success in its mission.
- They value a healthy, vibrant, and active developer and user community.
- They have made a long-term, recurring time investment to improve the project.
- They spend their time doing what needs to be done to ensure the
  project's success, not necessarily what is the most interesting or
  fun.
- A core reviewer's responsibility doesn't end with merging code.

Core Reviewer Expectations
--------------------------

Members of the core reviewer team are expected to:

- Attend and participate in the weekly IRC meetings (if your timezone allows)
- Monitor and participate in-channel at #openstack-horizon
- Monitor and participate in [Horizon] discussions on the mailing list
- Participate in related design summit sessions at the OpenStack
  Summits and Project Team Gatherings
- Review patch submissions actively and consistently

Please note in-person attendance at design summits, mid-cycles, and
other code sprints is not a requirement to be a core reviewer.
Participation can also include contributing to the design documents
discussed at the design sessions.

Active and consistent review of review activity, bug triage and other
activity will be performed monthly and fed back to the Core Reviewer Team
so everyone knows how things are progressing.

Code Merge Responsibilities
---------------------------

While everyone is encouraged to review changes, members of the core
reviewer team have the ability to +2/-2 and +A changes to these
repositories. This is an extra level of responsibility not to be taken
lightly. Correctly merging code requires not only understanding the
code itself, but also how the code affects things like documentation,
testing, upgrade impacts and interactions with other projects. It also
means you pay attention to release milestones and understand if a
patch you are merging is marked for the release, especially critical
during the feature freeze.
