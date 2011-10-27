#!/usr/bin/env python
"""Generates files for sphinx documentation using a simple Autodoc based
template.

To use, just run as a script:
    $ python doc/generate_autodoc_index.py
"""

import os


base_dir = os.path.dirname(os.path.abspath(__file__))
RSTDIR = os.path.join(base_dir, "source", "sourcecode")
SRCS = {'dashboard': os.path.join(base_dir, "..", "openstack-dashboard"),
        'django_openstack': os.path.join(base_dir, "..", "django-openstack")}


def find_autodoc_modules(module_name, sourcedir):
    """returns a list of modules in the SOURCE directory"""
    modlist = []
    os.chdir(os.path.join(sourcedir, module_name))
    print "SEARCHING %s" % sourcedir
    for root, dirs, files in os.walk("."):
        for filename in files:
            if filename.endswith(".py"):
                # root = ./dashboard/test/unit
                # filename = base.py
                # remove the pieces of the root
                elements = root.split(os.path.sep)
                # replace the leading "." with the module name
                elements[0] = module_name
                # and get the base module name
                base, extension = os.path.splitext(filename)
                if not (base == "__init__"):
                    elements.append(base)
                result = ".".join(elements)
                #print result
                modlist.append(result)
    return modlist

if not(os.path.exists(RSTDIR)):
    os.mkdir(RSTDIR)

INDEXOUT = open("%s/autoindex.rst" % RSTDIR, "w")
INDEXOUT.write("Source Code Index\n")
INDEXOUT.write("=================\n")
INDEXOUT.write(".. toctree::\n")
INDEXOUT.write("   :maxdepth: 1\n")
INDEXOUT.write("\n")

for modulename in SRCS:
    for module in find_autodoc_modules(modulename, SRCS[modulename]):
        generated_file = "%s/%s.rst" % (RSTDIR, module)
        print "Generating %s" % generated_file

        INDEXOUT.write("   %s\n" % module)
        FILEOUT = open(generated_file, "w")
        FILEOUT.write("The :mod:`%s` Module\n" % module)
        FILEOUT.write("=============================="
                      "=============================="
                      "==============================\n")
        FILEOUT.write(".. automodule:: %s\n" % module)
        FILEOUT.write("  :members:\n")
        FILEOUT.write("  :undoc-members:\n")
        FILEOUT.write("  :show-inheritance:\n")
        FILEOUT.close()

INDEXOUT.close()
