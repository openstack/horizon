This folder contains default policies of back-end services.
They are generated based on policy-in-code in back-end services.
Operators are not expected to edit them.

To update these files, run the following command:

 python manage.py dump_default_policies \
   --namespace <service> \
   --output-file openstack_dashboard/conf/default_policies/<service>.yaml

<service> must be a namespace under oslo.policy.policies to query and
we use "keystone", "nova", "cinder", "neutron" and "glance".
