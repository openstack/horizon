==============
Horizon Basics
==============

Values
======

    "Think simple" as my old master used to say - meaning reduce
    the whole of its parts into the simplest terms, getting back
    to first principles.

    -- Frank Lloyd Wright

Horizon holds several key values at the core of its design and architecture:

    * Core Support: Out-of-the-box support for all core OpenStack projects.
    * Extensible: Anyone can add a new component as a "first-class citizen".
    * Manageable: The core codebase should be simple and easy-to-navigate.
    * Consistent: Visual and interaction paradigms are maintained throughout.
    * Stable: A reliable API with an emphasis on backwards-compatibility.
    * Usable: Providing an *awesome* interface that people *want* to use.

The only way to attain and uphold those ideals is to make it *easy* for
developers to implement those values.

History
=======

Horizon started life as a single app to manage OpenStack's compute project.
As such, all it needed was a set of views, templates, and API calls.

From there it grew to support multiple OpenStack projects and APIs gradually,
arranged rigidly into "dash" and "syspanel" groupings.

During the "Diablo" release cycle an initial plugin system was added using
signals to hook in additional URL patterns and add links into the "dash"
and "syspanel" navigation.

This incremental growth served the goal of "Core Support" phenomenally, but
left "Extensible" and "Manageable" behind. And while the other key values took
shape of their own accord, it was time to re-architect for an extensible,
modular future.


The Current Architecture & How It Meets Our Values
==================================================

At its core, **Horizon should be a registration pattern for
applications to hook into**. Here's what that means and how it is
implemented in terms of our values:

Core Support
------------

Horizon ships with three central dashboards, a "User Dashboard", a
"System Dashboard", and a "Settings" dashboard. Between these three they
cover the core OpenStack applications and deliver on Core Support.

The Horizon application also ships with a set of API abstractions
for the core OpenStack projects in order to provide a consistent, stable set
of reusable methods for developers. Using these abstractions, developers
working on Horizon don't need to be intimately familiar with the APIs of
each OpenStack project.

Extensible
----------

A Horizon dashboard application is based around the :class:`~horizon.Dashboard`
class that provides a consistent API and set of capabilities for both
core OpenStack dashboard apps shipped with Horizon and equally for third-party
apps. The :class:`~horizon.Dashboard` class is treated as a top-level
navigation item.

Should a developer wish to provide functionality within an existing dashboard
(e.g. adding a monitoring panel to the user dashboard) the simple registration
pattern makes it possible to write an app which hooks into other dashboards
just as easily as creating a new dashboard. All you have to do is import the
dashboard you wish to modify.

Manageable
----------

Within the application, there is a simple method for registering a
:class:`~horizon.Panel` (sub-navigation items). Each panel contains the
necessary logic (views, forms, tests, etc.) for that interface. This granular
breakdown prevents files (such as ``api.py``) from becoming thousands of
lines long and makes code easy to find by correlating it directly to the
navigation.

Consistent
----------

By providing the necessary core classes to build from, as well as a
solid set of reusable templates and additional tools (base form classes,
base widget classes, template tags, and perhaps even class-based views)
we can maintain consistency across applications.

Stable
------

By architecting around these core classes and reusable components we
create an implicit contract that changes to these components will be
made in the most backwards-compatible ways whenever possible.

Usable
------

Ultimately that's up to each and every developer that touches the code,
but if we get all the other goals out of the way then we are free to focus
on the best possible experience.

.. seealso::

    :doc:`Quickstart <quickstart>`
        A short guide to getting started with using Horizon.

    :doc:`Frequently Asked Questions <faq>`
        Common questions and answers.

    :doc:`Glossary <glossary>`
        Common terms and their definitions.
