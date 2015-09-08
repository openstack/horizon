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

Cons:

* Difficult and time-consuming to create a repeatable test environment.
* Did I mention that setting it up is a pain?

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
