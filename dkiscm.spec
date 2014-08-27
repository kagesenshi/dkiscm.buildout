# How to build it
# QA_RPATHS=$[ 0x0001|0x0002 ] rpmbuild -bb platcdp.spec

Name:		mdec-scm
Version:	4.0b1
Release:	1%{?dist}
Summary:	MDEC Skills Competency Matrix

Group:		Applications/Internet
License:	GPLv2+
URL:		http://www.koslab.org
Source0:	%{name}-%{version}.tar.bz2

BuildRequires:	git python-devel python python-virtualenv python-setuptools
BuildRequires:  gcc gcc-c++ libxslt-devel libxml2-devel
BuildRequires:  libjpeg-turbo-devel libpng-devel zlib-devel bzip2-devel tk-devel
BuildRequires:  freetype-devel rubygems ghostscript wget openldap-devel
Requires:       %{name}-libs
Requires:       haproxy varnish 
Requires:       python-virtualenv wv
Requires(post): chkconfig
Requires(postun) : chkconfig

%description
A Plone distribution for MDEC Skills Competency Matrix

%package libs

Summary: Libraries and eggs for %{name}
Group:  System Environment/Libraries
Requires(pre): shadow-utils glibc-common
Requires(postun): shadow-utils

%description libs
Precompiled libraries and eggs for %{name}

%package eggbasket

Summary: Downloaded source tarballs used by %{name}
Group: System Environment/Libraries

%description eggbasket
Source tarballs and config files used for building %{name}

%prep
%setup -q

%build
mkdir -p %{buildroot}/%{_datadir}/%{name}/template/
cp -r * %{buildroot}/%{_datadir}/%{name}/template/

# build eggs
virtualenv --no-site-packages .
wget http://downloads.buildout.org/2/bootstrap.py -O bootstrap.py
./bin/python bootstrap.py
cat site.cfg.sample | sed 's|/var/lib/msc-scm/data|`pwd`/var|g' \
    | sed 's|/var/log/msc-scm/|`pwd`/var/log|' >  site.cfg 

cat << EOF > build.cfg
[buildout]
extends=deployment.cfg
eggs-directory=eggs
download-cache=downloads
extends-cache=downloads
EOF
mkdir downloads/
./bin/buildout -vvvv -U -c build.cfg
rm site.cfg

%install

# create directories
mkdir -p %{buildroot}/%{_bindir}/
mkdir -p %{buildroot}/%{_var}/lib/%{name}/eggs/
mkdir -p %{buildroot}/%{_var}/lib/%{name}/data/
mkdir -p %{buildroot}/%{_var}/lib/%{name}/backups/
mkdir -p %{buildroot}/%{_var}/cache/%{name}/
mkdir -p %{buildroot}/%{_var}/www/%{name}/
mkdir -p %{buildroot}/%{_sysconfdir}/init.d/
mkdir -p %{buildroot}/%{_sysconfdir}/%{name}/
mkdir -p %{buildroot}/%{_var}/log/%{name}

# copy built eggs
cp -r eggs/* %{buildroot}/%{_var}/lib/%{name}/eggs/

# copy tarballs
cp -r downloads/* %{buildroot}/%{_var}/cache/%{name}

# create deployment buildout 
rm -f %{buildroot}/%{_datadir}/%{name}/template/site.cfg
cp -r %{buildroot}/%{_datadir}/%{name}/template/* %{buildroot}/%{_var}/www/%{name}/
cp %{buildroot}/%{_var}/www/%{name}/site.cfg.sample %{buildroot}/%{_sysconfdir}/%{name}/msc-scm.cfg
rm -f %{buildroot}/%{_var}/www/%{name}/site.cfg
ln -s %{_sysconfdir}/%{name}/msc-scm.cfg %{buildroot}/%{_var}/www/%{name}/site.cfg 

# create buildout default.cfg
mkdir -p %{buildroot}/%{_var}/lib/%{name}/.buildout/
cat << EOF > %{buildroot}/%{_var}/lib/%{name}/.buildout/default.cfg 
[buildout]
download-cache = %{_var}/cache/%{name}/
eggs-directory = %{_var}/lib/%{name}/eggs/
extends-cache = %{_var}/cache/%{name}/
EOF

# create buildscript

sed 's|@@BUILDOUT_ROOT@@|%{_var}/www/%{name}|g' scripts/msc-scm.sh > %{buildroot}/%{_bindir}/msc-scm

cat << EOF > %{buildroot}/%{_sysconfdir}/init.d/msc-scm
#! /bin/bash
#
# msc-scm       Bring up/down msc-scm
#
# chkconfig: 345 99 01
# description: init script for msc-scm

. /etc/init.d/functions

case "\$1" in 
   start)
       %{_bindir}/msc-scm start
   ;;
   stop)
       %{_bindir}/msc-scm stop
   ;;
   restart)
       %{_bindir}/msc-scm restart
   ;;
   status)
       %{_bindir}/msc-scm status
   ;;
esac

EOF

rm -f %{buildroot}/%{_sysconfdir}/%{name}/site.cfg

%files
%defattr(-, plone, plone, -)
%{_datadir}/%{name}/template
%{_var}/www/%{name}
%config %{_sysconfdir}/%{name}/msc-scm.cfg
%attr(755, root, root) %{_bindir}/msc-scm
%attr(755, root, root) %{_sysconfdir}/init.d/msc-scm


%files libs
%defattr(-, plone, plone, -)
%{_var}/lib/%{name}
%dir %{_var}/cache/%{name}
%{_var}/log/%{name}

%files eggbasket
%defattr(-, plone, plone, -)
%{_var}/cache/%{name}

%pre
getent group plone >/dev/null || /usr/sbin/groupadd -r plone
getent passwd plone >/dev/null || /usr/sbin/useradd -r -g plone -d %{_var}/lib/%{name}/ -s /bin/false plone

%pre libs
getent group plone >/dev/null || /usr/sbin/groupadd -r plone
getent passwd plone >/dev/null || /usr/sbin/useradd -r -g plone -d %{_var}/lib/%{name}/ -s /bin/false plone

%post
chkconfig --add msc-scm

%postun 
chkconfig --del msc-scm >/dev/null 2>&1 || :

%postun libs 
userdel plone >/dev/null 2>&1 || :

%changelog

