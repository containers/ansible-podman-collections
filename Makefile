PKG_NAME=ansible-podman-collections
TMPINSTALLDIR=/tmp/$(PKG_NAME)-fpm-install
VERSION ?= $(shell python3 setup.py --version 2>/dev/null | sed "s/\([0-9]\+\.[0-9]\+\.[0-9]\+\).*/\1/g")

rpm:
	rm -rf $(TMPINSTALLDIR)
	mkdir -p ~/rpmbuild/SOURCES/
	mkdir -p $(TMPINSTALLDIR)/$(PKG_NAME)-$(VERSION)
	cp -r * $(TMPINSTALLDIR)/$(PKG_NAME)-$(VERSION)/
	tar -zcvf ~/rpmbuild/SOURCES/$(VERSION).tar.gz -C $(TMPINSTALLDIR) $(PKG_NAME)-$(VERSION)
	cp ansible-collection-containers-podman.spec ansible-collection-containers-podman-build.spec
	sed -i "s/Version:.*/Version:        $(VERSION)/g" ansible-collection-containers-podman-build.spec
	sed -i "s/Release:.*/Release:        999%{?dist}/g" ansible-collection-containers-podman-build.spec
	sed -i "s/^version: .*/version: $(VERSION)/" $(TMPINSTALLDIR)/$(PKG_NAME)-$(VERSION)/galaxy.yml
	rpmbuild -bb ansible-collection-containers-podman-build.spec
