============================================================
Horizon Policy Enforcement (RBAC: Role Based Access Control)
============================================================

Introduction
============

Horizon's policy enforcement builds on the oslo-incubator policy engine.
The basis of which is ``openstack_dashboard/openstack/common/policy.py``.
Services in OpenStack use the oslo policy engine to define policy rules
to limit access to APIs based primarily on role grants and resource
ownership.

The Keystone v3 API provides an interface for creating/reading/updating
policy files in the keystone database. However, at this time services
do not load the policy files into Keystone. Thus, the implementation in
Horizon is based on copies of policy.json files found in the service's
source code. The long-term goal is to read/utilize/update these policy
files in Horizon.

The service rules files are loaded into the policy engine to determine
access rights to actions and service APIs.

Horizon Settings
================

There are a few settings that must be in place for the Horizon policy
engine to work.

``POLICY_FILES_PATH``
---------------------

Default:  ``os.path.join(ROOT_PATH, "conf")``

Specifies where service based policy files are located.  These are used to
define the policy rules actions are verified against.  This value must contain
the files listed in ``POLICY_FILES`` or all policy checks will pass.

.. note::

    The path to deployment specific policy files can be specified in
    ``local_settings.py`` to override the default location.


``POLICY_FILES``
----------------

Default: ``{'identity': 'keystone_policy.json', 'compute': 'nova_policy.json'}``

This should essentially be the mapping of the contents of ``POLICY_FILES_PATH``
to service types.  When policy.json files are added to the directory
``POLICY_FILES_PATH``, they should be included here too. Without this mapping,
there is no way to map service types with policy rules, thus two policy.json
files containing a "default" rule would be ambiguous.

.. note::

    Deployment specific policy files can be specified in ``local_settings.py``
    to override the default policy files. It is imperative that these policy
    files match those deployed in the target OpenStack installation. Otherwise,
    the displayed actions and the allowed action will not match.

``POLICY_CHECK_FUNCTION``
-------------------------

Default: ``policy.check``

This value should not be changed, although removing it would be a means to
bypass all policy checks.


How user's roles are determined
===============================

Each policy check uses information about the user stored on the request to
determine the user's roles. This information was extracted from the scoped
token received from Keystone when authenticating.

Entity ownership is also a valid role. To verify access to specific entities
like a project, the target must be specified. See the section
:ref:`rule targets <rule_targets>` later in this document.

How to Utilize RBAC
===================

The primary way to add role based access control checks to panels is in the
definition of table actions. When implementing a derived action class,
setting the :attr:`~horizon.tables.Action.policy_rules` attribute to valid
policy rules will force a policy check before the
:meth:`horizon.tables.Action.allowed` method is called on the action. These
rules are defined in the policy files pointed to by ``POLICY_PATH`` and
``POLICY_FILES``. The rules are role based, where entity owner is also a
role. The format for the ``policy_rules`` is a list of two item tuples. The
first component of the tuple is the scope of the policy rule, this is the
service type. This informs the policy engine which policy file to reference.
The second component is the rule to enforce from the policy file specified by
the scope. An example tuple is::

    ("identity", "identity:get_user")

x tuples can be added to enforce x rules.

.. note::

    If a rule specified is not found in the policy file, the policy check
    will return False and the action will not be allowed.

The secondary way to add a role based check is to directly use the
:meth:`~openstack_dashboard.policy.check` method.  The method takes a list
of actions, same format as the :attr:`~horizon.tables.Action.policy_rules`
attribute detailed above; the current request object; and a dictionary of
action targets. This is the method that :class:`horizon.tables.Action` class
utilizes.  Examples look like::

    from openstack_dashboard import policy

    allowed = policy.check((("identity", "identity:get_user"),
                           ("identity", "identity:get_project"),), request)

    can_see = policy.check((("identity", "identity:get_user"),), request,
                           target={"domain_id": domainId})

.. note::

    Any time multiple rules are specified in a single `policy.check` method
    call, the result is the logical `and` of each rule check. So, if any
    rule fails verification, the result is `False`.

.. _rule_targets:

Rule Targets
============

Some rules allow access if the user owns the entity. Policy check targets
specify particular entities to check for user ownership. The target parameter
to the :meth:`~openstack_dashboard.policy.check` method is a simple dictionary.
For instance, the target for checking access a project looks like::

    {"project_id": "0905760626534a74979afd3f4a9d67f1"}

If the value matches the ``project_id`` to which the user's token is scoped,
then access is allowed.

When deriving the :class:`horizon.tables.Action` class for use in a table, if
a policy check is desired for a particular target, the implementer should
override the :meth:`horizon.tables.Action.get_policy_target` method. This
allows a programmatic way to specify the target based on the current datum. The
value returned should be the target dictionary.
