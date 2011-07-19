PYTHON=`which python`
DESTDIR=/
BUILDIR=$(CURDIR)/debian/django-openstack
PROJECT=django-openstack

all:
	@echo "make buildout - Run through buildout"
	@echo "make test - Run tests"
	@echo "make source - Create source package"
	@echo "make install - Install on local system"
	@echo "make buildrpm - Generate a rpm package"
	@echo "make builddeb - Generate a deb package"
	@echo "make clean - Get rid of scratch and byte files"

buildout: ./bin/buildout
	./bin/buildout

./bin/buildout:
	$(PYTHON) bootstrap.py

source:
	$(PYTHON) setup.py sdist $(COMPILE)

install:
	$(PYTHON) setup.py install --root $(DESTDIR) $(COMPILE)

buildrpm:
	$(PYTHON) setup.py bdist_rpm --post-install=rpm/postinstall --pre-uninstall=rpm/preuninstall

builddeb:
	# build the source package in the parent directory
	# then rename it to project_version.orig.tar.gz
	$(PYTHON) setup.py sdist $(COMPILE) --dist-dir=../
	rename -f 's/$(PROJECT)-(.*)\.tar\.gz/$(PROJECT)_$$1\.orig\.tar\.gz/' ../*
	# build the package
	#dpkg-buildpackage -i -I -rfakeroot
	dpkg-buildpackage -b -rfakeroot -tc -uc -D

clean:
	$(PYTHON) setup.py clean
	$(MAKE) -f $(CURDIR)/debian/rules clean
	rm -rf build/ MANIFEST
	find . -name '*.pyc' -delete
