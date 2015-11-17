Packaging generalities
======================

Packaging can easily be understood as: you are an engineer building a car.
Unfortunately, you don't have anything else, other than a manual and very
few tools. Any more specific tool you will require to actually build your car
has to be created, too.

As example, if you are going to add a library named "foo", it has to be

 - Free Software
 - All tools required to build it, have to be provided (as package) as well.
 - actively maintained, i.e. we need an active and responsive upstream.
 - It should NOT require a specific file system layout, FHS applies.

Embedded copies
---------------

Imagine if all packages had a local copy of jQuery. If a security hole was
discovered in jQuery, then we would have to write more than 90 patches in
Debian (as more than 90 packages are depending on jQuery). This is simply
not practical. Therefore, it is not acceptable to purely copy code from
other repositories into any software code (and no, Horizon cannot be a
special case). This tends to become a fork, diverging from its real
upstream. The main reason for this is that it's not being maintained, and if a
bug is discovered in original upstream, it can't easily be fixed by updating
just a single package.

Another reason not to simply copy a library into Horizon source code is, it
might have conflicting licenses. Distributing sources with conflicting
licenses in one tarball will revoke rights in best case. In worst case,
one might be liable.


Why did we decide to use XStatic?
---------------------------------

There's a bunch of problems that are addressed by XStatic, which would
have to be addressed if we are to find a new solution. Non-exhaustively,
XStatic provides these things which are inherently not available by default
with systems like NPM, Grunt and such:

 - Dependency checks: The general rule makes it possible to check that
   dependencies (including fonts, JavaScript libs, etc.) are available in
   downstream distributions. The current XStatic system enables these checks.
 - Reusable components across projects: The XStatic system ensures
   components are reusable by other packages (ie: non-Horizon things,
   like Fuel for example).
 - System-wide registry of static content: XStatic brings a system-wide
   registry of components, so it is easy to check if one is missing (ie:
   no egg-info, broken package dependency, etc.). Currently, NPM doesn't
   offer this.
 - No embedded contents: The XStatic system makes sure we aren't embedding
   files which are already available in the distribution (ie: libjs-* or
   fonts-* packages). It even provides a compatibility layer for
   distributions. Not every distribution places static files in the same
   position of the file system.
   On the other side, if you are packaging an XStatic package for your
   distribution, make sure, you are using distribution provided static files.
   Having put together something as XStatic package is *no* guarantee to
   get it into a distribution. Preferably, XStatic provides only the
   abstraction layer to use distribution provided static files.
 - Package build systems are disconnected from the outside network (for several
   reasons).

If you want to redesign a new system to replace XStatic, please keep the
above 4 points in mind. The new system *must* keep these features: please
don't sacrifice them just because it's more convenient for Horizon
developers. Yes, XStatic are making your life harder, we understand that.
But we really need the above.


Free software
-------------

Red Hat, Debian, and SUSE distributions are made only of free software (free
as in Libre, or free speech). This means that not only the software we
include in our repository is free, but also all the tools that are used are
free as well, and also available in the distribution. As package maintainers
care about the quality of the packages they upload, they do run the unit
tests which are available from upstream repositories. This also qualifies test
requirements as build requirements, i.e. the same rules apply for building
the software as for the software itself. Build requirements not included in
the distribution are not allowed.

One famous example is Selenium. For a long time, it was only available from
the non-free repositories of Debian. The reason was that upstream included
some .xpi binaries. These .xpi included some Windows .dll and Linux .so
files. As they couldn't be rebuilt from source, the whole of python-selenium
was declared non-free. If we made Horizon build-depends on python-selenium,
this would mean Horizon wouldn't be in Debian main anymore (remember:
contrib and non-free are *not* considered part of Debian). Recently, the
package maintainer of python-selenium decided to remove the .xpi files from
python-selenium, and upload it to Debian Experimental (this time, in main,
not in non-free). So if it was possible for Horizon to use python-selenium
(without the non-free .xpi files), then we could run Selenium tests at
package build time.


Running unit tests at build time
--------------------------------

The build environment inside a distribution isn't exactly the same as the
one in the OpenStack gate. For example, versions of a given library can be
slightly different from the one in the gate. And we do want to detect when
this is a problem, so it can be fixed. So whenever possible, try to make the
lives of package maintainer easier, and allow them (or help them) to run
unit tests when it is possible.


Minified JavaScript policy
--------------------------

In all free software distribution which actively maintain OpenStack
packages (ie: at least RDO, Debian, and Ubuntu), minified JavaScript are
considered non-free. This means that they should *not* be present in
upstream source code, or at least, a non-minified version should be present
next to the minified version. Also, you should be aware of potential
security issues with minifiers. This `blog post`_ explains it very well.

 .. _`blog post`: https://zyan.scripts.mit.edu/blog/backdooring-js/


Component version
-----------------

One very important thing to take care about, is the version of all the
components you will use in your app. Since it is not acceptable to embed a
given component within Horizon, then we must use what's in the distribution
(including all fonts, JavaScript, etc.). This is where it becomes a bit
tricky.

In most distribution, it is not acceptable to have multiple version of the
same piece of software.

In Red Hat systems, it is technically possible to install 2 versions of
one library at the same time, but a few restrictions apply, especially for
usage.  However, package maintainers try to avoid this as much as possible.
For package dependency resolution, it might be necessary to provide packages
for depending packages as well. For example, if you had Django-1.4 and
Django-1.8 in the same release, you would have to provide Horizon built for
Django-1.4 and another package providing Horizon built for Django-1.8. This
is a high effort and needs to be evaluated carefully.

In Debian, it is generally forbidden to have multiple versions of the same
library in the same Debian release; there are very few specific exceptions
to that rule.

This has consequences for an upstream author willing to integrate their
software in a downstream distribution. The best situation is when it is
possible to support whatever version is currently available in the target
distributions, up to the latest version upstream. Declaring lower
and upper bounds within your requirements.txt doesn't solve the issue. It
allows all the tests to pass on gate because they are run against a narrow set
of versions in requirements.txt, while the downstream distribution may still
have some dependencies with versions outside of the range specified in
requirements.txt - which may lead to failures not caught in the OpenStack gate.

When it's not possible to support all versions of a library (because it would
be too much work, or when it would then be very hard to test in the gate),
then the best recommendation is to use whatever is available inside the
target distributions. For example, Horizon currently supports
jQuery >= 1.7.2, as this is what is currently available in Debian Jessie
and Ubuntu Trusty (the last LTS).

One would search in a distribution for a piece of software foo using a command
like ``dnf search foo``, or ``zypper se -s foo``. ``dnf info foo`` returns
more detailed information about the package.



Filesystem Hierarchy Standards
------------------------------

Every distribution has to comply with the FHS (Filesystem Hierarchy
Standards). This defines a set of rules which we *must* follow as package
maintainers. Some of the most important ones are:

 - /usr should be considered as read only, and no software should write in it
   at runtime (however, it is fine for a package post installation script
   to write there). As a consequence, distributions had to write many
   tricks to convince horizon to write in /var/lib only (for example:
   writing symlinks to /var/lib/openstack-dashboard, or patch the default
   local_settings.py to write the SECRET_KEY in /var).
 - Configuration should always be in /etc, no matter what. As a consequence,
   package maintainers had to place symlinks to
   /etc/openstack-dashboard/local_settings in Red Hat based distributions
   instead of using directly
   /usr/share/openstack-dashboard/openstack_dashboard/local/local_settings.py
   which Horizon expects. In Debian the configuration file is named
   /etc/openstack-dashboard/local_settings.py


Packaging Horizon for distributions
-----------------------------------

Horizon is a python module. It will preferably be installed at default
location for python; e.g in Fedora and openSUSE, this is
/usr/lib/python2.7/site-packages/horizon, and in Debian/Ubuntu it is
/usr/lib/python2.7/dist-packages/horizon.

Configuration files should live under /etc/openstack-dashboard; policy files
should be created and modified there as well.

It is expected that ``manage.py collectstatic`` will be executed during
package build.
This is the `recommended way`_ for Django applications.
Depending on configuration, it might be required to ``manage.py compress``
during package build, too.

 .. _`recommended way`: https://docs.djangoproject.com/en/1.8/howto/static-files/deployment/
