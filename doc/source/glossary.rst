========
Glossary
========

Horizon

    The OpenStack dashboard project. Also the name of the top-level
    Python object which handles registration for the app.

Dashboard

    A Python class representing a top-level navigation item (e.g. "project")
    which provides a consistent API for Horizon-compatible applications.

Panel

    A Python class representing a sub-navigation item (e.g. "instances")
    which contains all the necessary logic (views, forms, tests, etc.) for
    that interface.

Project

    Used in user-facing text in place of the term "Tenant" which is Keystone's
    word.
