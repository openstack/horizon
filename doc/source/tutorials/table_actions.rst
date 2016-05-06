============================================
Tutorial: Adding a complex action to a table
============================================

This tutorial covers how to add a more complex action to a table, one that requires
an action and form definitions, as well as changes to the view, urls, and table.

This tutorial assumes you have already completed :doc:`Building a Dashboard using
Horizon  </tutorials/dashboard>`. If not, please do so now as we will be modifying the
files created there.

This action will create a snapshot of the instance. When the action is taken,
it will display a form that will allow the user to enter a snapshot name,
and will create that snapshot when the form is closed using the ``Create snapshot``
button.

Defining the view
=================

To define the view, we must create a view class, along with the template (``HTML``)
file and the form class for that view.

The template file
-----------------
The template file contains the HTML that will be used to show the view.

Create a ``create_snapshot.html`` file under the ``mypanel/templates/mypanel``
directory and add the following code::

    {% extends 'base.html' %}
    {% load i18n %}
    {% block title %}{% trans "Create Snapshot" %}{% endblock %}

    {% block page_header %}
      {% include "horizon/common/_page_header.html" with title=_("Create a Snapshot") %}
    {% endblock page_header %}

    {% block main %}
        {% include 'mydashboard/mypanel/_create_snapshot.html' %}
    {% endblock %}


As you can see, the main body will be defined in ``_create_snapshot.html``,
so we must also create that file under the ``mypanel/templates/mypanel``
directory. It should contain the following code::

    {% extends "horizon/common/_modal_form.html" %}
    {% load i18n %}

    {% block modal-body-right %}
        <h3>{% trans "Description:" %}</h3>
        <p>{% trans "Snapshots preserve the disk state of a running instance." %}</p>
    {% endblock %}


The form
--------

Horizon provides a :class:`~horizon.forms.base.SelfHandlingForm` class which simplifies
some of the details involved in creating a form. Our form will derive from this
class, adding a character field to allow the user to specify a name for the
snapshot, and handling the successful closure of the form by calling the nova
api to create the snapshot.

Create the ``forms.py`` file under the ``mypanel`` directory and add the following::

    from django.core.urlresolvers import reverse
    from django.utils.translation import ugettext_lazy as _

    from horizon import exceptions
    from horizon import forms

    from openstack_dashboard import api


    class CreateSnapshot(forms.SelfHandlingForm):
        instance_id = forms.CharField(label=_("Instance ID"),
                                      widget=forms.HiddenInput(),
                                      required=False)
        name = forms.CharField(max_length=255, label=_("Snapshot Name"))

        def handle(self, request, data):
            try:
                snapshot = api.nova.snapshot_create(request,
                                                    data['instance_id'],
                                                    data['name'])
                return snapshot
            except Exception:
                exceptions.handle(request,
                                  _('Unable to create snapshot.'))


The view
--------

Now, the view will tie together the template and the form. Horizon provides a
:class:`~horizon.forms.views.ModalFormView` class which simplifies the creation of a
view that will contain a modal form.

Open the ``views.py`` file under the ``mypanel`` directory and add the code
for the CreateSnapshotView and the necessary imports. The complete
file should now look something like this::

    from django.core.urlresolvers import reverse
    from django.core.urlresolvers import reverse_lazy
    from django.utils.translation import ugettext_lazy as _

    from horizon import tabs
    from horizon import exceptions
    from horizon import forms

    from horizon.utils import memoized

    from openstack_dashboard import api

    from openstack_dashboard.dashboards.mydashboard.mypanel \
        import forms as project_forms

    from openstack_dashboard.dashboards.mydashboard.mypanel \
        import tabs as mydashboard_tabs


    class IndexView(tabs.TabbedTableView):
        tab_group_class = mydashboard_tabs.MypanelTabs
        # A very simple class-based view...
        template_name = 'mydashboard/mypanel/index.html'

        def get_data(self, request, context, *args, **kwargs):
            # Add data to the context here...
            return context


    class CreateSnapshotView(forms.ModalFormView):
        form_class = project_forms.CreateSnapshot
        template_name = 'mydashboard/mypanel/create_snapshot.html'
        success_url = reverse_lazy("horizon:project:images:index")
        modal_id = "create_snapshot_modal"
        modal_header = _("Create Snapshot")
        submit_label = _("Create Snapshot")
        submit_url = "horizon:mydashboard:mypanel:create_snapshot"

        @memoized.memoized_method
        def get_object(self):
            try:
                return api.nova.server_get(self.request,
                                           self.kwargs["instance_id"])
            except Exception:
                exceptions.handle(self.request,
                                  _("Unable to retrieve instance."))

        def get_initial(self):
            return {"instance_id": self.kwargs["instance_id"]}

        def get_context_data(self, **kwargs):
            context = super(CreateSnapshotView, self).get_context_data(**kwargs)
            instance_id = self.kwargs['instance_id']
            context['instance_id'] = instance_id
            context['instance'] = self.get_object()
            context['submit_url'] = reverse(self.submit_url, args=[instance_id])
            return context


Adding the url
==============

We must add the url for our new view.  Open the ``urls.py`` file under
the ``mypanel`` directory and add the following as a new url pattern::

    url(r'^(?P<instance_id>[^/]+)/create_snapshot/$',
        views.CreateSnapshotView.as_view(),
        name='create_snapshot'),

The complete ``urls.py`` file should look like this::

    from django.conf.urls import url

    from openstack_dashboard.dashboards.mydashboard.mypanel import views


    urlpatterns = [,
        url(r'^$',
            views.IndexView.as_view(), name='index'),
        url(r'^(?P<instance_id>[^/]+)/create_snapshot/$',
            views.CreateSnapshotView.as_view(),
            name='create_snapshot'),
    ]



Define the action
=================

Horizon provides a :class:`~horizon.tables.LinkAction` class which simplifies
adding an action which can be used to display another view.

We will add a link action to the table that will be accessible from each row
in the table. The action will use the view defined above to create a snapshot
of the instance represented by the row in the table.

To do this, we must edit the ``tables.py`` file under the ``mypanel`` directory
and add the following::

    def is_deleting(instance):
        task_state = getattr(instance, "OS-EXT-STS:task_state", None)
        if not task_state:
            return False
        return task_state.lower() == "deleting"


    class CreateSnapshotAction(tables.LinkAction):
        name = "snapshot"
        verbose_name = _("Create Snapshot")
        url = "horizon:mydashboard:mypanel:create_snapshot"
        classes = ("ajax-modal",)
        icon = "camera"

        # This action should be disabled if the instance
        # is not active, or the instance is being deleted
        def allowed(self, request, instance=None):
            return instance.status in ("ACTIVE") \
                and not is_deleting(instance)


We must also add our new action as a row action for the table::

    row_actions = (CreateSnapshotAction,)


The complete ``tables.py`` file should look like this::

    from django.utils.translation import ugettext_lazy as _

    from horizon import tables


    def is_deleting(instance):
        task_state = getattr(instance, "OS-EXT-STS:task_state", None)
        if not task_state:
            return False
        return task_state.lower() == "deleting"


    class CreateSnapshotAction(tables.LinkAction):
        name = "snapshot"
        verbose_name = _("Create Snapshot")
        url = "horizon:mydashboard:mypanel:create_snapshot"
        classes = ("ajax-modal",)
        icon = "camera"

        def allowed(self, request, instance=None):
            return instance.status in ("ACTIVE") \
                and not is_deleting(instance)


    class MyFilterAction(tables.FilterAction):
        name = "myfilter"


    class InstancesTable(tables.DataTable):
        name = tables.Column("name", verbose_name=_("Name"))
        status = tables.Column("status", verbose_name=_("Status"))
        zone = tables.Column('availability_zone', verbose_name=_("Availability Zone"))
        image_name = tables.Column('image_name', verbose_name=_("Image Name"))

        class Meta:
            name = "instances"
            verbose_name = _("Instances")
            table_actions = (MyFilterAction,)
            row_actions = (CreateSnapshotAction,)


Run and check the dashboard
===========================

We must once again run horizon to verify our dashboard is working::

    ./run_tests.sh --runserver 0.0.0.0:8877


Go to ``http://<your server>:8877`` using a browser. After login as an admin,
display ``My Panel`` to see the ``Instances`` table. For every ``ACTIVE``
instance in the table, there will be a ``Create Snapshot`` action on the row.
Click on ``Create Snapshot``, enter a snapshot name in the form that is shown,
then click to close the form. The ``Project Images`` view should be shown with
the new snapshot added to the table.


Conclusion
==========

What you've learned here is the fundamentals of how to add a table action that
requires a form for data entry. This can easily be expanded from creating a
snapshot to other API calls that require more complex forms to gather the
necessary information.

If you have feedback on how this tutorial could be improved, please feel free
to submit a bug against ``Horizon`` in `launchpad`_.

    .. _launchpad: https://bugs.launchpad.net/horizon
