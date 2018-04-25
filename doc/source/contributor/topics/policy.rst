.. _topics-policy:

============================================================
Horizon Policy Enforcement (RBAC: Role Based Access Control)
============================================================

Introduction
============

Horizon's policy enforcement builds on the oslo_policy engine.
The basis of which is ``openstack_auth/policy.py``.
Services in OpenStack use the oslo policy engine to define policy rules
to limit access to APIs based primarily on role grants and resource
ownership.

The implementation in Horizon is based on copies of policy files
found in the service's source code.

The service rules files are loaded into the policy engine to determine
access rights to actions and service APIs.

Horizon Settings
================

There are a few settings that must be in place for the Horizon policy
engine to work.

* ``POLICY_CHECK_FUNCTION``
* ``POLICY_DIRS``
* ``POLICY_FILES_PATH``
* ``POLICY_FILES``

For more detail, see :doc:`/configuration/settings`.

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

Django: Table action
--------------------

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

Django: policy check function
-----------------------------

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

Angular: ifAllowed method
-------------------------

The third way to add a role based check is in javascript files. Use the method
'ifAllowed()' in file 'openstack_dashboard.static.app.core.policy.service.js'.
The method takes a list of actions, similar format with the
:attr:`~horizon.tables.Action.policy_rules` attribute detailed above.
An Example looks like::

    angular
    .module('horizon.dashboard.identity.users')
    .controller('identityUsersTableController', identityUsersTableController);

    identityUsersTableController.$inject = [
      'horizon.app.core.openstack-service-api.policy',
    ];

    function identityUsersTableController(toast, gettext, policy, keystone) {
      var rules = [['identity', 'identity:list_users']];
      policy.ifAllowed({ rules: rules }).then(policySuccess, policyFailed);
    }

Angular: hz-if-policies
-----------------------

The fourth way to add a role based check is in html files. Use angular
directive 'hz-if-policies' in file
'openstack_dashboard/static/app/core/cloud-services/hz-if-policies.directive.js'.
Assume you have the following policy defined in your angular controller::

    ctrl.policy = { rules: [["identity", "identity:update_user"]] }

Then in your HTML, use it like so::

    <div hz-if-policies='ctrl.policy'>
      <span>I am visible if the policy is allowed!</span>
    </div>

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

Policy file maintenance
=======================

The policy implementation uses the copies of policies defined in
back-end services.

As of Queens, the OpenStack community are in the process of
`policy-in-code <https://governance.openstack.org/tc/goals/queens/policy-in-code.html>`__.
Some projects already define their policies in the code,
and some still have their policies in ``policy.json`` files.

For project with the legacy ``policy.json`` files,
what we need to do is just to copy ``policy.json`` into the horizon tree.

For projects with "policy-in-code", all policies are defined as python codes,
so we first need to generate policy files with its default rules.
To do this, run the following command after install a corresponding project.

.. code-block:: console

   oslopolicy-sample-generator --namespace $PROJECT --format json \
       --output-file $HORIZON_REPO/openstack_dashboard/conf/$PROJECT_policy.json

After syncing policies from back-end services, you need to check what are
changed. If a policy referred by horizon has been changed, you need to check
and modify the horizon code base accordingly.
To summarize which policies are removed or added, a convenient tool is
provided:

.. code-block:: console

   $ cd openstack_dashboard/conf/
   $ python ../../tools/policy-diff.py --help
   usage: policy-diff.py [-h] --old OLD --new NEW [--mode {add,remove}]

   optional arguments:
   -h, --help           show this help message and exit
   --old OLD            Current policy file
   --new NEW            New policy file
   --mode {add,remove}  Diffs to be shown

   # Show removed policies
   # The default is "--mode remove". You can omit --mode option.
   $ python ../../tools/policy-diff.py \
       --old keystone_policy.json --new keystone_policy.json.new --mode remove
   default
   identity:change_password
   identity:get_identity_provider
