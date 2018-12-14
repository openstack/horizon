==================
Packaging Software
==================


Software packages
-----------------

This section describes some general things that a developer should know about
packaging software. This content is mostly derived from best practices.

A developer building a package is comparable to an engineer building a car
with only a manual and very few tools. If the engineer needs a specific tool
to build the car, he must create the tool, too.

As a developer, if you are going to add a library named "foo", the package
must adhere to the following standards:

- Be a free package created with free software.
- Include all tools that are required to build the package.
- Have an active and responsive upstream to maintain the package.
- Adhere to Filesystem Hierarchy Standards (FHS). A specific file system
  layout is not required.


Embedded copies not allowed
---------------------------

Imagine if all packages had a local copy of jQuery. If a security hole is
discovered in jQuery, we must write more than 90 patches in Debian, one for
each package that includes a copy. This is simply not practical. Therefore,
it is unacceptable for Horizon to copy code from other repositories when
creating a package. Copying code from another repository tends to create a
fork, diverging from the upstream code. The fork includes code that is not
being maintained, so if a bug is discovered in the original upstream, it
cannot easily be fixed by updating a single package.

Another reason to avoid copying a library into Horizon source code is that
it might create conflicting licenses. Distributing sources with conflicting
licenses in one tarball revokes rights in best case. In the worst case, you
could be held legally responsible.


Free software
-------------

Red Hat, Debian, and SUSE distributions are made only of free software (free
as in Libre, or free speech). The software that we include in our repository
is free. The tools are also free, and available in the distribution.

Because package maintainers care about the quality of the packages we upload,
we run tests that are available from upstream repositories. This also
qualifies test requirements as build requirements. The same rules apply for
building the software as for the software itself. Special build requirements
that are not included in the overall distribution are not allowed.

An example of historically limiting, non-free software is Selenium. For a
long time, Selenium was only available from the non-free repositories of
Debian. The reason was that upstream included some .xpi binaries. These .xpi
included some Windows .dll and Linux .so files. Because they could not be
rebuilt from the source, all of python-selenium was declared non-free. If we
made Horizon build-depends on python-selenium, this would mean Horizon
wouldn't be in Debian main anymore (contrib and non-free are *not* considered
part of Debian). Recently, the package maintainer of python-selenium decided
to remove the .xpi files from python-selenium, and upload it to Debian
Experimental (this time, in main, not in non-free). If at some point it is
possible for Horizon to use python-selenium (without the non-free .xpi files),
then we could run Selenium tests at package build time.


Running unit tests at build time
--------------------------------

The build environment inside a distribution is not exactly the same as the
one in the OpenStack gate. For example, versions of a given library can be
slightly different from the one in the gate. We want to detect when
problematic differences exist so that we can fix them. Whenever possible, try
to make the lives of the package maintainer easier, and allow them (or help
them) to run unit tests.


Minified JavaScript policy
--------------------------

In free software distributions that actively maintain OpenStack packages (such
as RDO, Debian, and Ubuntu), minified JavaScript is considered non-free. This
means that minified JavaScript should *not* be present in upstream source
code. At the very least, a non-minified version should be present next to the
minified version. Also, be aware of potential security issues with minifiers.
This `blog post`_ explains it very well.

.. _`blog post`: https://diracdeltas.github.io/blog/backdooring-js/


Component version
-----------------

Be careful about the version of all the components you use in your
application. Since it is not acceptable to embed a given component within
Horizon, we must use what is in the distribution, including all fonts,
JavaScript, etc. This is where it becomes a bit tricky.

In most distributions, it is not acceptable to have multiple versions of the
same piece of software. In Red Hat systems, it is technically possible to
install 2 versions of one library at the same time, but a few restrictions
apply, especially for usage. However, package maintainers try to avoid
multiple versions as much as possible. For package dependency resolution, it
might be necessary to provide packages for depending packages as well. For
example, if you had Django-1.4 and Django-1.8 in the same release, you must
provide Horizon built for Django-1.4 and another package providing Horizon
built for Django-1.8. This is a large effort and needs to be evaluated
carefully.

In Debian, it is generally forbidden to have multiple versions of the same
library in the same Debian release. Very few exceptions exist.

Component versioning has consequences for an upstream author willing to
integrate their software in a downstream distribution. The best situation
is when it is possible to support whatever version is currently available
in the target distributions, up to the latest version upstream. Declaring
lower and upper bounds within your requirements.txt does not solve the issue.
It allows all the tests to pass on gate because they are run against a narrow
set of versions in requirements.txt. The downstream distribution might still
have some dependencies with versions outside of the range that is specified
in requirements.txt. These dependencies may lead to failures that are not
caught in the OpenStack gate.

At times it might not be possible to support all versions of a library. It
might be too much work, or it might be very hard to test in the gate. In this
case, it is best to use whatever is available inside the target distributions.
For example, Horizon currently supports jQuery >= 1.7.2, as this is what is
currently available in Debian Jessie and Ubuntu Trusty (the last LTS).

You can search in a distribution for a piece of software foo using a command
like ``dnf search foo``, or ``zypper se -s foo``. ``dnf info foo`` returns
more detailed information about the package.


Filesystem Hierarchy Standards
------------------------------

Every distribution must comply with the Filesystem Hierarchy Standards (FHS).
The FHS defines a set of rules that we *must* follow as package
maintainers. Some of the most important ones are:

- /usr is considered read only. Software must not write in /usr at
  runtime. However, it is fine for a package post-installation script to write
  in /usr. When this rule was not followed, distributions had to write many
  tricks to convince Horizon to write in ``/var/lib`` only. For example,
  distributions wrote symlinks to ``/var/lib/openstack-dashboard``, or patched
  the default ``local_settings.py`` to write the ``SECRET_KEY`` in /var.
- Configuration must always be in /etc, no matter what. When this rule
  was not followed, package maintainers had to place symlinks to
  ``/etc/openstack-dashboard/local_settings`` in Red Hat based distributions
  instead of using directly
  ``/usr/share/openstack-dashboard/openstack_dashboard/local/local_settings.py``
  which Horizon expects. In Debian,the configuration file is named
  ``/etc/openstack-dashboard/local_settings.py.``


Packaging Horizon
-----------------


Why we use XStatic
~~~~~~~~~~~~~~~~~~

XStatic provides the following features that are not currently available
by default with systems like NPM and Grunt:

- Dependency checks: XStatic checks that dependencies, such as fonts
  and JavaScript libs, are available in downstream distributions.
- Reusable components across projects: The XStatic system ensures
  components are reusable by other packages, like Fuel.
- System-wide registry of static content: XStatic brings a system-wide
  registry of components, so that it is easy to check if one is missing. For
  example, it can detect if there is no egg-info, or a broken package
  dependency exists.
- No embedded content: The XStatic system helps us avoid embedding files that
  are already available in the distribution, for example, libjs-* or fonts-*
  packages. It even provides a compatibility layer for distributions. Not
  every distribution places static files in the same position in the file
  system. If you are packaging an XStatic package for your distribution, make
  sure that you are using the static files provided by that specific
  distribution. Having put together an XStatic package is *no* guarantee to
  get it into a distribution. XStatic provides only the abstraction layer to
  use distribution provided static files.
- Package build systems are disconnected from the outside network (for
  several reasons). Other packaging systems download dependencies directly
  from the internet without verifying that the downloaded file is intact,
  matches a provided checksum, etc. With these other systems, there is no way
  to provide a mirror, a proxy or a cache, making builds even more unstable
  when minor networking issues are encountered.

The previous features are critical requirements of the Horizon packaging
system. Any new system *must* keep these features. Although XStatic may mean
a few additional steps from individual developers, those steps help maintain
consistency and prevent errors across the project.


Packaging Horizon for distributions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Horizon is a Python module. Preferably, it is installed at the default
location for python. In Fedora and openSUSE, this is
``/usr/lib/python2.7/site-packages/horizon``, and in Debian/Ubuntu it is
``/usr/lib/python2.7/dist-packages/horizon``.

Configuration files should reside under ``/etc/openstack-dashboard``.
Policy files should be created and modified there as well.

It is expected that ``manage.py collectstatic`` will be run during package
build.
This is the `recommended way`_ for Django applications.
Depending on configuration, it might be required to ``manage.py compress``
during package build, too.

.. _`recommended way`: https://docs.djangoproject.com/en/dev/howto/static-files/deployment/
