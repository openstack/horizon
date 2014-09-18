==========================
Frequently Asked Questions
==========================

What is the relationship between ``Dashboards``, ``Panels``, and navigation?

    The navigational structure is strongly encouraged to flow from
    ``Dashboard`` objects as top-level navigation items to ``Panel`` objects as
    sub-navigation items as in the current implementation. Template tags
    are provided to automatically generate this structure.

    That said, you are not required to use the provided tools and can write
    templates and URLconfs by hand to create any desired structure.

Does a panel have to be an app in ``INSTALLED_APPS``?

    A panel can live in any Python module. It can be a standalone which ties
    into an existing dashboard, or it can be contained alongside others within
    a larger dashboard "app". There is no strict enforcement here. Python
    is "a language for consenting adults." A module containing a Panel does
    not need to be added to ``INSTALLED_APPS``, but this is a common and
    convenient way to load a standalone panel.

Could I hook an external service into a panel using, for example, an iFrame?

    Panels are just entry-points to hook views into the larger dashboard
    navigational structure and enforce common attributes like RBAC. The
    view and corresponding templates can contain anything you would like,
    including iFrames.

What does this mean for visual design?

    The ability to add an arbitrary number of top-level navigational items
    (``Dashboard`` objects) poses a new design challenge. Horizon's lead
    designer has taken on the challenge of providing a reference design
    for Horizon which supports this possibility.

What browsers are supported?

    Horizon is primarily tested and supported on the latest version of Firefox,
    the latest version of Chrome, and IE9+. Issues related to Safari and Opera
    will also be considered. The list of supported browsers and versions is
    informally documented on the `Browser Support wiki page
    <https://wiki.openstack.org/wiki/Horizon/BrowserSupport>`_.

