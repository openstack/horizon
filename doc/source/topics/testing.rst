===================
Testing Topic Guide
===================

Having good tests in place is absolutely critical for ensuring a stable,
maintainable codebase. Hopefully that doesn't need any more explanation.

However, what defines a "good" test is not always obvious, and there are
a lot of common pitfalls that can easily shoot your test suite in the
foot.

If you already know everything about testing but are fed up with trying to
debug why a specific test failed, you can skip the intro and jump
straight to :ref:`debugging_unit_tests`.

An overview of testing
======================

There are three main types of tests, each with their associated pros and cons:

Unit tests
----------

These are isolated, stand-alone tests with no external dependencies. They are
written from the perspective of "knowing the code", and test the assumptions
of the codebase and the developer.

Pros:

* Generally lightweight and fast.
* Can be run anywhere, anytime since they have no external dependencies.

Cons:

* Easy to be lax in writing them, or lazy in constructing them.
* Can't test interactions with live external services.

Functional tests
----------------

These are generally also isolated tests, though sometimes they may interact
with other services running locally. The key difference between functional
tests and unit tests, however, is that functional tests are written from the
perspective of the user (who knows nothing about the code) and only knows
what they put in and what they get back. Essentially this is a higher-level
testing of "does the result match the spec?".

Pros:

* Ensures that your code *always* meets the stated functional requirements.
* Verifies things from an "end user" perspective, which helps to ensure
  a high-quality experience.
* Designing your code with a functional testing perspective in mind helps
  keep a higher-level viewpoint in mind.

Cons:

* Requires an additional layer of thinking to define functional requirements
  in terms of inputs and outputs.
* Often requires writing a separate set of tests and/or using a different
  testing framework from your unit tests.
* Doesn't offer any insight into the quality or status of the underlying code,
  only verifies that it works or it doesn't.

Integration Tests
-----------------

This layer of testing involves testing all of the components that your
codebase interacts with or relies on in conjunction. This is equivalent to
"live" testing, but in a repeatable manner.

Pros:

* Catches *many* bugs that unit and functional tests will not.
* Doesn't rely on assumptions about the inputs and outputs.
* Will warn you when changes in external components break your code.
* Will take screenshot of the current page on test fail for easy debug

Cons:

* Difficult and time-consuming to create a repeatable test environment.
* Did I mention that setting it up is a pain?

Screenshot directory could be set through horizon.conf file, default value:
 "./integration_tests_screenshots"

So what should I write?
-----------------------

A few simple guidelines:

#. Every bug fix should have a regression test. Period.

#. When writing a new feature, think about writing unit tests to verify
   the behavior step-by-step as you write the feature. Every time you'd
   go to run your code by hand and verify it manually, think "could I
   write a test to do this instead?". That way when the feature is done
   and you're ready to commit it you've already got a whole set of tests
   that are more thorough than anything you'd write after the fact.

#. Write tests that hit every view in your application. Even if they
   don't assert a single thing about the code, it tells you that your
   users aren't getting fatal errors just by interacting with your code.

What makes a good unit test?
============================

Limiting our focus just to unit tests, there are a number of things you can
do to make your unit tests as useful, maintainable, and unburdensome as
possible.

Test data
---------

Use a single, consistent set of test data. Grow it over time, but do everything
you can not to fragment it. It quickly becomes unmaintainable and perniciously
out-of-sync with reality.

Make your test data as accurate to reality as possible. Supply *all* the
attributes of an object, provide objects in all the various states you may want
to test.

If you do the first suggestion above *first* it makes the second one far less
painful. Write once, use everywhere.

To make your life even easier, if your codebase doesn't have a built-in
ORM-like function to manage your test data you can consider building (or
borrowing) one yourself. Being able to do simple retrieval queries on your
test data is incredibly valuable.

Mocking
-------

Mocking is the practice of providing stand-ins for objects or pieces of code
you don't need to test. While convenient, they should be used with *extreme*
caution.

Why? Because overuse of mocks can rapidly land you in a situation where you're
not testing any real code. All you've done is verified that your mocking
framework returns what you tell it to. This problem can be very tricky to
recognize, since you may be mocking things in ``setUp`` methods, other modules,
etc.

A good rule of thumb is to mock as close to the source as possible. If you have
a function call that calls an external API in a view , mock out the external
API, not the whole function. If you mock the whole function you've suddenly
lost test coverage for an entire chunk of code *inside* your codebase. Cut the
ties cleanly right where your system ends and the external world begins.

Similarly, don't mock return values when you could construct a real return
value of the correct type with the correct attributes. You're just adding
another point of potential failure by exercising your mocking framework instead
of real code. Following the suggestions for testing above will make this a lot
less burdensome.

Assertions and verification
---------------------------

Think long and hard about what you really want to verify in your unit test. In
particular, think about what custom logic your code executes.

A common pitfall is to take a known test object, pass it through your code,
and then verify the properties of that object on the output. This is all well
and good, except if you're verifying properties that were untouched by your
code. What you want to check are the pieces that were *changed*, *added*, or
*removed*. Don't check the object's id attribute unless you have reason to
suspect it's not the object you started with. But if you added a new attribute
to it, be damn sure you verify that came out right.

It's also very common to avoid testing things you really care about because
it's more difficult. Verifying that the proper messages were displayed to the
user after an action, testing for form errors, making sure exception handling
is tested... these types of things aren't always easy, but they're extremely
necessary.

To that end, Horizon includes several custom assertions to make these tasks
easier. :meth:`~openstack_dashboard.test.helpers.TestCase.assertNoFormErrors`,
:meth:`~horizon.test.helpers.TestCase.assertMessageCount`, and
:meth:`~horizon.test.helpers.TestCase.assertNoMessages` all exist for exactly
these purposes. Moreover, they provide useful output when things go wrong so
you're not left scratching your head wondering why your view test didn't
redirect as expected when you posted a form.

.. _debugging_unit_tests:

Debugging Unit Tests
====================

Tips and tricks
---------------

#. Use :meth:`~openstack_dashboard.test.helpers.TestCase.assertNoFormErrors`
   immediately after your ``client.post`` call for tests that handle form views.
   This will immediately fail if your form POST failed due to a validation error
   and tell you what the error was.

#. Use :meth:`~horizon.test.helpers.TestCase.assertMessageCount` and
   :meth:`~horizon.test.helpers.TestCase.assertNoMessages` when a piece of code
   is failing inexplicably. Since the core error handlers attach user-facing
   error messages (and since the core logging is silenced during test runs)
   these methods give you the dual benefit of verifying the output you expect
   while clearly showing you the problematic error message if they fail.

#. Use Python's ``pdb`` module liberally. Many people don't realize it works
   just as well in a test case as it does in a live view. Simply inserting
   ``import pdb; pdb.set_trace()`` anywhere in your codebase will drop the
   interpreter into an interactive shell so you can explore your test
   environment and see which of your assumptions about the code isn't,
   in fact, flawlessly correct.

#. If the error is in the Selenium test suite, you're likely getting very little
   information about the error. To increase the information provided to you,
   edit ``horizon/test/settings.py`` to set ``DEBUG = True`` and set the logging
   level to 'DEBUG' for the default 'test' logger. Also, add a logger config
   for Django::

         },
         'loggers': {
    +        'django': {
    +            'handlers': ['test'],
    +            'propagate': False,
    +        },
             'django.db.backends': {

Common pitfalls
---------------

There are a number of typical (and non-obvious) ways to break the unit tests.
Some common things to look for:

#. Make sure you stub out the method exactly as it's called in the code
   being tested. For example, if your real code calls
   ``api.keystone.tenant_get``, stubbing out ``api.tenant_get`` (available
   for legacy reasons) will fail.

#. When defining the expected input to a stubbed call, make sure the
   arguments are *identical*, this includes ``str`` vs. ``int`` differences.

#. Make sure your test data are completely in line with the expected inputs.
   Again, ``str`` vs. ``int`` or missing properties on test objects will
   kill your tests.

#. Make sure there's nothing amiss in your templates (particularly the
   ``{% url %}`` tag and its arguments). This often comes up when refactoring
   views or renaming context variables. It can easily result in errors that
   you might not stumble across while clicking around the development server.

#. Make sure you're not redirecting to views that no longer exist, e.g.
   the ``index`` view for a panel that got combined (such as instances &
   volumes).

#. Make sure your mock calls are in order before calling ``mox.ReplayAll``.
   The order matters.

#. Make sure you repeat any stubbed out method calls that happen more than
   once. They don't automatically repeat, you have to explicitly define them.
   While this is a nuisance, it makes you acutely aware of how many API
   calls are involved in a particular function.

Understanding the output from ``mox``
-------------------------------------

Horizon uses ``mox`` as its mocking framework of choice, and while it
offers many nice features, its output when a test fails can be quite
mysterious.

Unexpected Method Call
~~~~~~~~~~~~~~~~~~~~~~

This occurs when you stubbed out a piece of code, and it was subsequently
called in a way that you didn't specify it would be. There are two reasons
this tends to come up:

#. You defined the expected call, but a subtle difference crept in. This
   may be a string versus integer difference, a string versus unicode
   difference, a slightly off date/time, or passing a name instead of an id.

#. The method is actually being called *multiple times*. Since mox uses
   a call stack internally, it simply pops off the expected method calls to
   verify them. That means once a call is used once, it's gone. An easy way
   to see if this is the case is simply to copy and paste your method call a
   second time to see if the error changes. If it does, that means your method
   is being called more times than you think it is.

Expected Method Never Called
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This one is the opposite of the unexpected method call. This one means you
told mox to expect a call and it didn't happen. This is almost always the
result of an error in the conditions of the test. Using the
:meth:`~openstack_dashboard.test.helpers.TestCase.assertNoFormErrors` and
:meth:`~horizon.test.helpers.TestCase.assertMessageCount` will make it readily
apparent what the problem is in the majority of cases. If not, then use ``pdb``
and start interrupting the code flow to see where things are getting off track.

Integration tests in Horizon
============================

The integration tests currently live in the Horizon repository, see `here`_,
which also contains instructions on how to run the tests. To make integration
tests more understandable and maintainable, the Page Object pattern is used
throughout them.

Horizon repository also provides two shell `scripts`_, which are executed in
pre_test_hook and post_test_hook respectively. Pre hook is generally used for
modifying test environment, while post hook is used for running actual
integration tests with tox and collecting test artifacts. Thanks to the
incorporating all modifications to tests into Horizon repository, one can alter
both tests and test environment and see the immediate results in Jenkins job
output.

.. _here: https://github.com/openstack/horizon/tree/master/openstack_dashboard/test/integration_tests
.. _scripts: https://github.com/openstack/horizon/tree/master/tools/gate/integration

Page Object pattern
-------------------

Within any web application's user interface (UI) there are areas that the tests
interact with. A Page Object simply models these as objects within the test
code. This reduces the amount of duplicated code; if the UI changes, the fix
needs only be applied in one place.

Page Objects can be thought of as facing in two directions simultaneously.
Facing towards the developer of a test, they represent the services offered by
a particular page. Facing away from the developer, they should be the only
thing that has a deep knowledge of the structure of the HTML of a page (or
part of a page). It is simplest to think of the methods on a Page Object as
offering the "services" that a page offers rather than exposing the details
and mechanics of the page. As an example, think of the inbox of any web-based
email system. Amongst the services that it offers are typically the ability to
compose a new email, to choose to read a single email, and to list the subject
lines of the emails in the inbox. How these are implemented should not matter
to the test.

Writing reusable and maintainable Page Objects
----------------------------------------------

Because the main idea is to encourage the developer of a test to try and think
about the services that they are interacting with rather than the
implementation, Page Objects should seldom expose the underlying WebDriver
instance. To facilitate this, methods on the Page Object should return other
Page Objects. This means that we can effectively model the user's journey
through the application.

Another important thing to mention is that a Page Object need not represent an
entire page. It may represent a section that appears many times within a site
or page, such as site navigation. The essential principle is that there is
only one place in your test suite with knowledge of the structure of the HTML
of a particular (part of a) page. With this in mind, a test developer builds
up regions that become reusable components (`example of a base form`_). These
properties can then be redefined or overridden (e.g. selectors) in the actual
pages (subclasses) (`example of a tabbed form`_).

The page objects are read-only and define the read-only and clickable elements
of a page, which work to shield the tests. For instance, from the test
perspective, if "Logout" used to be a link but suddenly becomes an option in a
drop-down menu, there are no changes (in the test itself) because it still simply
calls the "click_on_logout" action method.

This approach has two main aspects:

* The classes with the actual tests should be as readable as possible
* The other parts of the testing framework should be as much about data as
  possible, so that if the CSS etc. changes you only need to change that one
  property. If the flow changes, only the action method should need to change.

There is little that is Selenium-specific in the Pages, except for the
properties. There is little coupling between the tests and the pages. Writing
the tests becomes like writing out a list of steps (by using the previously
mentioned action methods). One of the key points, particularly important for
this kind of UI driven testing is to isolate the tests from what is behind
them.

.. _example of a base form: https://github.com/openstack/horizon/blob/8.0.0/openstack_dashboard/test/integration_tests/regions/forms.py#L250
.. _example of a tabbed form: https://github.com/openstack/horizon/blob/8.0.0/openstack_dashboard/test/integration_tests/regions/forms.py#L322

List of references
------------------

* https://wiki.openstack.org/wiki/Horizon/Testing/UI#Page_Object_Pattern_.28Selected_Approach.29
* https://wiki.mozilla.org/QA/Execution/Web_Testing/Docs/Automation/StyleGuide#Page_Objects
* https://code.google.com/p/selenium/wiki/PageObjects

Debugging integration tests
===========================

Even perfectly designed Page Objects are not a guarantee that your integration
test will not ever fail. This can happen due to different causes:

The first and most anticipated kind of failure is the inability to perform a
testing scenario by a living person simply because some OpenStack service or
Horizon itself prevents them from doing so. This is exactly the kind that
integration tests are designed to catch. Let us call them "good" failures.

All other kinds of failures are unwanted and could be roughly split into the
two following categories:

#. The failures that occur due to changes in application's DOM. some CSS/ Xpath selectors no longer matching
   Horizon app's DOM. The usual signature for that kind of failures is having
   a DOM changing patch for which the test job fails with a message like
   this `selenium.common.exceptions.NoSuchElementException: Message: Unable to
   locate element: {"method":"css selector","selector":"div.modal-dialog"}`.
   If you find yourself in such a situation, you should fix the Page Object
   selectors according to the DOM changes you made.

#. Unfortunately it is still quite possible to get the above error for a patch
   which didn't implement any DOM changes. Among the reasons of such behavior
   observed in past were:

   * Integration tests relying on relative ordering of form fields and table
     actions that broke with the addition of a new field. This issue should
     be fixed by now, but may reappear in future for different entities.

   * Integration tests relying on popups disappearing by the time a specific
     action needs to be taken (or not existing at all). This expectation
     turned out to be very fragile, since the speed of tests execution by
     Jenkins workers may change independently of integration test code (hence,
     popups disappear too late to free the way for the next action). The
     unexpected (both too long and too short) timeouts aren't limited to just
     popups, but apply to every situation when the element state transition
     is not instant (like opening an external link, going to another page in
     Horizon, waiting for button to become active, waiting for a table row to
     change its state). Luckily, most transitions of "element becomes visible/
     emerge to existence from non-existence" kind are already bulletproofed
     using `implicit_wait` parameter in `integration_tests/horizon.conf` file.
     Selenium just waits for specified amount of seconds for an element to
     become visible (if it's not already visible) giving up when it exceeds
     (with the above error). Also it's worth mentioning `explicit_wait` parameter
     which is considered when the selenium `wait_until` method is involved (and
     it is used, e.g. in waiting for spinner and messages popups to disappear).

An inconvenient thing about reading test results in the `console.html` file
attached to every `gate-horizon-dsvm-integration` finished job is that the test
failure may appear either as failure (assertion failed), or as error (expected
element didn't show up). In both cases an inquirer should suspect a legitimate
failure first (i.e., treat errors as failures). Unfortunately, no clear method
exists for the separation of "good" from from "bad" failures. Each case is
unique and full of mysteries.

The Horizon testing mechanism tries to alleviate this ambiguity by providing
several facilities to aid in failure investigation:

* First there comes a screenshot made for every failed test (in a separate
  folder, on a same level as `console.html`) - almost instant snapshot of a
  screen on the moment of failure (*almost* sometimes matters, especially in
  a case of popups that hang on a screen for a limited time);
* Then the patient inquirer may skim through the vast innards of
  `console.html`, looking at browser log first (all javascript and css errors
  should come there),
* Then looking at a full textual snapshot of a page for which test failed
  (sometimes it gives a more precise picture than a screenshot),
* And finally looking at test error stacktrace (most useful) and a lengthy
  output of requests/ responses with a selenium server. The last log sometimes
  might tell us how long a specific web element was polled before failing (in
  case of `implicit_wait` there should be a series of requests to the same
  element).

The best way to solve the cause of test failure is running and debugging the
troublesome test locally. You could use `pdb` or Python IDE of your choice to
stop test execution in arbitrary points and examining various Page Objects
attributes to understand what they missed. Looking at the real page structure
in browser developer tools also could explain why the test fails. Sometimes it
may be worth to place breakpoints in JavaScript code (provided that static is
served uncompressed) to examine the objects of interest. If it takes long, you
may also want to increase the webdriver's timeout so it will not close browser
windows forcefully. Finally, sometimes it may make sense to examine the
contents of `logs` directory, especially apache logs - but that is mostly the
case for the "good" failures.

Writing your first integration test
===================================

So, you are going to write your first integration test and looking for some
guidelines on how to do it. The first and the most comprehensive source of
knowledge is the existing codebase of integration tests. Look how other tests
are written, which Page Objects they use and learn by copying. Accurate imitation
will eventually lead to a solid understanding. Yet there are few things that may
save you some time when you know them in advance.

File and directory layout and go_to_*page() methods
---------------------------------------------------
Below is the filesystem structure that test helpers rely on.::

  horizon/
  └─ openstack_dashboard/
     └─ test/
        └─ integration_tests/
           ├─ pages/
           │  ├─ admin/
           │  │  ├─ __init__.py
           │  │  └─ system/
           │  │     ├─ __init__.py
           │  │     └─ flavorspage.py
           │  ├─ project/
           │  │  └─ compute/
           │  │     ├─ __init__.py
           │  │     ├─ access_and_security/
           │  │     │  ├─ __init__.py
           │  │     │  └─ keypairspage.py
           │  │     └─ imagespage.py
           │  └─ navigation.py
           ├─ regions/
           ├─ tests/
           ├─ config.py
           └─ horizon.conf

New tests are put into integration_tests/tests, where they are grouped
by the kind of entities being tested (test_instances.py, test_networks.py, etc).
All Page Objects to be used by tests are inside pages/directory, the nested
directory structure you see within it obeys the value of `Navigation.CORE_PAGE_STRUCTURE`
you can find at pages/navigation.py module. The contents of the `CORE_PAGE_STRUCTURE`
variable should in turn mirror the structure of standard dashboard sidebar menu.
If this condition is not met, the go_to_<pagename>page() methods which are generated
automatically at runtime will have problems matching the real sidebar items. How are
these go_to_*page() methods are generated? From the sidebar's point of view, dashboard
content could be at most four levels deep: Dashboard, Panel Group, Panel and Tab.
Given the mixture of these entities in existing dashboards, it was decided that:

* When panels need to be addressed with go_to_<pagename>page() methods, two components in
  the method's name are enough for distinguishing the right path to go along, namely a Panel
  name and a Panel Group name (or a Dashboard name, if no Panel Group exists above Panel).
  For example,

  * `go_to_system_flavorspage()` method to go to Admin->System->Flavors and

  * `go_to_identity_projectspage()` method to go to Identity->Projects panel.

* When we need to go one level deeper, i.e. go to the specific TableTab on any panel that
  has several tabs, three components are enough - Panel Group, Panel and Tab names. For
  example, `go_to_compute_accessandsecurity_floatingipspage()` for navigating to
  Project->Compute->Access & Security->Floating IPs tab. Note that one cannot navigate
  to a Panel level if that Panel has several tabs (i.e., only terminal levels could be
  navigated to).

As you might have noticed, method name components are chosen from normalized items of
the `CORE_PAGE_STRUCTURE` dictionary, where normalization means replacing spaces with `_`
symbol and `&` symbol with `and`, then downcasing all symbols.

Once the `go_to_*page()` method's name is parsed and the proper menu item is matched in
a dashboard, it should return the proper Page Object. For that to happen a properly
named class should reside in a properly named module located in the right place of the
filesystem. More specifically and top down:

#. Page Object class is located in:

   * <dashboard>/<panel_group>/<panel>page.py file for non-tabbed pages

   * <dashboard>/<panel_group>/<panel>/<tab>page.py file for tabbed pages
     Values <dashboard>, <panel_group>, <panel> and <tab> are the normalized versions of
     the items from the `CORE_PAGE_STRUCTURE` dictionary.

#. Within the above module a descendant of `basepage.BaseNavigationPage` should be
   defined, its name should have the form <Panel>Page or <Tab>Page, where <Panel> and <Tab>
   are capitalized versions of normalized <panel> and <tab> items respectively.

Reusable regions
----------------

* `TableRegion` binds to the HTML Horizon table using the `TableRegion`'s `name`
  attribute. To bind to the proper table this attribute has to be the same as
  the `name` attribute of a `Meta` subclass of a corresponding `tables.DataTable`
  descendant in the Python code. `TableRegion` provides all the needed facilities for
  solving the following table-related tasks.

  * Getting a specific row from a table matched by the column name and a target
    text within that column (use `get_row()` method) or taking all the existing
    rows on a current table page with `rows` property.
  * Once you have a reference to a specific row, it can either be marked with
    `mark()` for further batch actions or split to cells (using `cells` property
    which is dictionary representing column name as a key to cell wrapper as a
    value).

  * For interacting with actions `TableRegion` provides 2 decorators, namely
    `@bind_table_action()` and `@bind_row_action()` which bind to the actual HTML
    button widget and decorate the specific table methods. These methods in turn
    should click a bound button (comes as these methods' second argument after `self`)
    and usually return a new region which is most often bound to a modal form
    being shown after clicking that button in real Horizon.

  * Another important part of `TableRegion` are the facilities for checking the
    properties of a paged table - `assert_definition()`, `is_next_link_available()`
    and `is_prev_link_available()` helpers and `turn_next_page()` / `turn_prev_page()`
    which obviously cause the next / prev table page to be shown.

* when interacting with modal and non-modal forms three flavors of form wrappers
  can be used.

  * `BaseFormRegion` is used for simplest forms which are usually 'Submit' /
    'Cancel' dialogs with no fields to be filled.

  * `FormRegion` is the most used wrapper which provides interaction with the
    fields within that form. Every field is backed by its own wrapper class, while
    the `FormRegion` acts as a container which initializes all the field wrappers in
    its `__init__()` method. Field mappings passed to `__init__()` could be

     * either a tuple of string labels, in that case the same label is used for
       referencing the field in test code and for binding to the HTML input (should be
       the same as `name` attribute of that widget, could be seen in Django code defining
       that form in Horizon)

     * or a dictionary, where the key will be used for referencing the test field
       and the value will be used for binding to the HTML input. Also it is feasible
       to provide values other than strings in that dictionary - in this case they are
       meant to be a Python class. This Python class will be initialized as any
       BaseRegion is usually initialized and then the value's key will be used for
       referencing this object. This is useful when dealing with non-standard widgets
       in forms (like Membership widget in Create/​Edit Project form or Networks widget
       in Launch Instance form).

  * `TabbedFormRegion` is a slight variation of `FormRegion`, it has several tabs
    and thus can accept a tuple of tuples / dictionaries of field mappings, where
    every tuple corresponds to a tab of a real form, binding order is that first
    tuple binds to leftmost tab, which has index 0. Passing `default_tab` other than
    0 to `TabbedFormRegion.__init__` we can make the test form to be created with
    the tab other than the leftmost being shown immediately. Finally the method `switch_to`
    allows us to switch to any existing form's tab.

* `MessageRegion` is a small region, but is very important for asserting that
  everything goes well in Horizon under test. Technically, the `find_message_and_dismiss`
  method belongs to `BasePage` class, but whenever it is called, `regions.messages`
  module is imported as well to pass a `messages.SUCCESS` / `messages.ERROR`
  argument into. The method returns `True` / `False` depending on if the specified
  message was found and dismissed (which could be then asserted for).

Customizing tests to a specific gate environment
------------------------------------------------

* Upstream gate environment is not the only possible environment where Horizon
  integration tests can be run. Various downstream distributions may also
  want to run them. To ease the adoption of upstream tests to possibly
  different conditions of a downstream gate environment, integration tests use
  a configuration machinery backed by oslo.config library. It includes the
  following pieces of knowledge:

  * integration_tests/config.py file where all possible setting groups and
    settings are defined along with their descriptions and defaults. If you are
    going to add a new setting to Horizon integration tests, you should add it
    first to this file.

  * integration_tests/horizon.conf file - where all the overrides are
    actually located. For clarity its contents mirrors the default values
    in config.py (although technically they could be completely commented out
    with the same result).

  * To make developers' lives easier a local-only (not tracked by git)
    counterpart of horizon.conf could exist at the same directory, named
    'local-horizon.conf'. It is meant solely for overriding values from
    horizon.conf that a developer's environment might differ from the gate
    environment (like Horizon url or admin user password).

* When integration tests are run by openstack-infra/devstack-gate scripts they
  use 2 hooks to alter the devstack gate environment, namely pre_test_hook and
  post_test_hook. Contents of both hooks are defined inside the corresponding
  shell scripts located at 'tools/gate/integration' at the top-level of horizon
  repo. If you find yourself asking which of the hooks you need to modify - pre
  or post, keep the following things in mind.

  * Pre hook is executed before the Devstack is deployed, that essentially
    means that almost none of packages that are installed as OpenStack services
    dependencies during Devstack deployment are going to be present in the
    system. Yet all the repositories contained with `PROJECTS` variable defined
    in `devstack-vm-gate-wrap.sh`_ script will be already cloned by the moment
    pre hook is executed. So the natural use for it is to customize some Horizon
    settings before they are used in operations like compressing statics etc.

  * Post hook is executed after Devstack is deployed, so integration tests
    themselves are run inside that hook, as well as various test artifacts
    collection. When you modify it, do not forget to save the exit code of
    a tox integration tests run and emit at the end of the script - or you may
    lose the SUCCESS/FAILURE status of the whole tests suite and tamper with the
    job results!

.. _devstack-vm-gate-wrap.sh: https://github.com/openstack-infra/devstack-gate/blob/master/devstack-vm-gate-wrap.sh


Writing integration tests for Horizon plugins
---------------------------------------------

There are 2 possible setups when running integration tests for Horizon plugins.

The first setup, which is suggested to be used in gate of *-dashboard plugins
is to get horizon as a dependency of a plugin and then run integration tests
using horizon.conf config file inside the plugin repo. This way the plugin augments
the location of Horizon built-in Page Objects with the location of its own
Page Objects, contained within the `plugin_page_path` option and the Horizon
built-in nav structure with its own nav structure contained within
`plugin_page_structure`. Then the plugin integration tests are run against core
Horizon augmented with just this particular plugin content.

The second setup may be used when it is needed to run integration tests for
Horizon + several plugins. In other words, content from several plugins is
merged into core Horizon content, then the combined integration tests from core
Horizon and all the involved plugins are run against the resulting dashboards.
To make this possible both options `plugin_page_path` and
`plugin_page_structure` have MultiStrOpt type. This means that they may be
defined several times and all the specified values will be gathered in a list,
which is iterated over when running integration tests. In this setup it's easier to
run the tests from Horizon repo, using the horizon.conf file within it.

Also keep in mind that `plugin_page_structure` needs to be a strict JSON
string, w/o trailing commas etc.
