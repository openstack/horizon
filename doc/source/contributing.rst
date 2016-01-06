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

Whew! Got all that? Okay! You're good to go.

.. _`OpenStack Contributor License Agreement`: http://wiki.openstack.org/CLA
.. _`Horizon Developers`: https://launchpad.net/~horizon
.. _`instructions for setting up git-review`: http://docs.openstack.org/infra/manual/developers.html#development-workflow

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
* Help improve the `User Experience Design`_ or contribute to the `Persona Working Group`_.

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

* Make sure the unit tests pass: ``./run_tests.sh`` for Python, and ``npm run test`` for JS.
* Make sure the linting tasks pass: ``./run_tests.sh --pep8`` for Python, and ``npm run lint`` for JS.
* Make sure your code is ready for translation: ``./run_tests.sh --pseudo de`` See the Translatability section below for details.
* Make sure your code is up-to-date with the latest master: ``git pull --rebase``
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

.. _translatability:

Translatability
===============

Horizon gets translated into multiple languages. The pseudo translation tool
can be used to verify that code is ready to be translated. The pseudo tool
replaces a language's translation with a complete, fake translation. Then
you can verify that your code properly displays fake translations to validate
that your code is ready for translation.

Running the pseudo translation tool
-----------------------------------

#. Make sure your English po file is up to date: ``./run_tests.sh --makemessages``
#. Run the pseudo tool to create pseudo translations. For example, to replace the German translation with a pseudo translation: ``./run_tests.sh --pseudo de``
#. Compile the catalog: ``./run_tests.sh --compilemessages``
#. Run your development server.
#. Log in and change to the language you pseudo translated.

It should look weird. More specifically, the translatable segments are going
to start and end with a bracket and they are going to have some added
characters. For example, "Log In" will become "[~Log In~您好яшçあ]"
This is useful because you can inspect for the following, and consider if your
code is working like it should:

* If you see a string in English it's not translatable. Should it be?
* If you see brackets next to each other that might be concatenation. Concatenation
  can make quality translations difficult or impossible. See
  https://wiki.openstack.org/wiki/I18n/TranslatableStrings#Use_string_formating_variables.2C_never_perform_string_concatenation
  for additional information.
* If there is unexpected wrapping/truncation there might not be enough
  space for translations.
* If you see a string in the proper translated language, it comes from an
  external source. (That's not bad, just sometimes useful to know)
* If you get new crashes, there is probably a bug.

Don't forget to cleanup any pseudo translated po files. Those don't get merged!

Code Style
==========

As a project, Horizon adheres to code quality standards.

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

 ..  Note ::
     If typecasting is desired, explicit casting is preferred to keep the
     meaning of your code clear.

* Keep document reflows to a minimum. DOM manipulation is expensive, and can
  become a performance issue. If you are accessing the DOM, make sure that you
  are doing it in the most optimized way. One example is to build up a document
  fragment and then append the fragment to the DOM in one pass instead of doing
  multiple smaller DOM updates.

* Use “strict”, enclosing each JavaScript file inside a self-executing
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
       ::

         <div class="something"></div>
           $(".something").html("Don't find me this way!");

      Is better found like:
      ::

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
* Source-code formatting – (or “beautification”) is recommended but should be
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
  more detailed information, check the :doc:`topics/angularjs`.

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

* For localization in Angular files, use the Angular service
  horizon.framework.util.i18n.gettext. Ensure that the injected dependency
  is named ``gettext``. For regular Javascript files, use either ``gettext`` or
  ``ngettext``. Only those two methods are recognized by our tools and will be
  included in the .po file after running ``./run_tests --makemessages``.
  ::

    // Angular
    angular.module('myModule')
      .factory('myFactory', myFactory);

    myFactory.$inject = ['horizon.framework.util.i18n.gettext'];
    function myFactory(gettext) {
      gettext('translatable text');
    }

    // Javascript
    gettext(apple);
    ngettext('apple', 'apples', count);

    // Not valid
    var _ = gettext;
    _('translatable text');

    $window.gettext('translatable text');

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

JavaScript and CSS libraries
----------------------------

We do not bundle third-party code in Horizon's source tree. Instead, we package
the required files as XStatic Python packages and add them as dependencies to
Horizon. In particular, when you need to add a new third-party JavaScript or
CSS library to Horizon, follow those steps:

 1. Check if the library is already packaged as Xstatic on PyPi, by searching
    for the library name. If it already is, go to step 5. If it is, but not in
    the right version, contact the original packager.
 2. Package the library as an Xstatic package by following the instructions in
    Xstatic documentation_.
 3. `Create a new repository under OpenStack`_. Use "xstatic-core" and
    "xstatic-ptl" groups for the ACLs. Make sure to include the
    ``publish-to-pypi`` job.
 4. `Setup PyPi`_ to allow OpenStack to publish your package.
 5. `Tag your release`_. That will cause it to be automatically packaged and
    released to PyPi.
 6. Add the package to global-requirements_. Make sure to mention the license.
 7. Add the package to Horizon's ``requirements.txt`` file, to its
    ``settings.py``, and to the ``_scripts.html`` or ``_stylesheets.html``
    templates. Make sure to keep the order alphabetic.

.. warning::

    Note that once a package is released, you can not "un-release" it. You
    should never attempt to modify, delete or rename a released package without
    a lot of careful planning and feedback from all projects that use it.

    For the purpose of fixing packaging mistakes, XStatic has the build number
    mechanism. Simply fix the error, increment the build number and release the
    newer package.

.. _documentation: http://xstatic.rtfd.org/en/latest/packaging.html
.. _`Create a new repository under OpenStack`: http://docs.openstack.org/infra/manual/creators.html
.. _`Tag your release`: http://docs.openstack.org/infra/manual/drivers.html#tagging-a-release
.. _`Setup PyPi`: http://docs.openstack.org/infra/manual/creators.html#give-openstack-permission-to-publish-releases
.. _global-requirements: https://github.com/openstack/requirements/blob/master/global-requirements.txt

HTML
----

Again, readability is paramount; however be conscientious of how the browser
will handle whitespace when rendering the output. Two spaces is the preferred
indentation style to match all front-end code.

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
  ``:class:`~horizon.foo.Bar```) when referring to other Horizon components.
  The better-linked our docs are, the easier they are to use.

Be sure to generate the documentation before submitting a patch for review.
Unexpected warnings often appear when building the documentation, and slight
reST syntax errors frequently cause links or cross-references not to work
correctly.

Documentation is generated with Sphinx using the tox command. To create HTML docs and man pages:

.. code-block:: bash

    $ tox -e docs

The results are in the doc/build/html and doc/build/man directories respectively.

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

A release note is suggested if a long-standing or important bug is fixed.
Otherwise, a release note is not required.

Horizon uses `reno <http://docs.openstack.org/developer/reno/usage.html>`_ to
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
