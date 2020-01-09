%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

%if 0%{?fedora} >= 19 || 0%{?rhel} >= 7
%bcond_without  systemd
%endif

%global commit 097381d336017ba772dffd439e316120b639ffbd
%global shortcommit %(c=%{commit}; echo ${c:0:7})

Summary:        Registry server for Docker
Name:           docker-registry
Version:        0.6.8
Release:        8%{?dist}
License:        ASL 2.0
URL:            https://github.com/dotcloud/docker-registry
Source:         https://github.com/lsm5/docker-registry/archive/%{commit}/docker-registry-%{shortcommit}.tar.gz
Source1:        docker-registry.service
Source2:        docker-registry.sysconfig
Source3:        docker-registry.sysvinit

# Support for older Redis Python binding in EPEL
Patch0:         Support-for-older-Redis-Python-binding.patch

BuildRequires:    python2-devel

%if %{with systemd}
BuildRequires:      systemd
Requires(post):     systemd
Requires(preun):    systemd
Requires(postun):   systemd
%else
Requires(post):     chkconfig
Requires(preun):    chkconfig
Requires(postun):   initscripts
%endif

Requires:       m2crypto
Requires:       PyYAML
Requires:       python-requests
Requires:       python-gunicorn
Requires:       python-gevent
Requires:       python-blinker
Requires:       python-backports-lzma
Requires:       python-jinja2
Requires:       python-flask

BuildArch:      noarch

%description
Registry server for Docker (hosting/delivering of repositories and images).

%prep
%setup -q -n docker-registry-%{commit}

# Remove the golang implementation
# It's not the main one (yet?)
rm -rf contrib/golang_impl

%if !%{with systemd}
%patch0 -p1
%endif

%install
install -d %{buildroot}%{_bindir}
install -d %{buildroot}%{_sysconfdir}/sysconfig
install -d %{buildroot}%{_sharedstatedir}/%{name}
install -d %{buildroot}%{python_sitelib}/%{name}

install -m 644 %{SOURCE2} %{buildroot}%{_sysconfdir}/sysconfig/%{name}

%if %{with systemd}
install -d %{buildroot}%{_unitdir}
install -m 644 %{SOURCE1} %{buildroot}%{_unitdir}/%{name}.service

# Make sure we set proper WorkingDir in the systemd service file
sed -i "s|#WORKDIR#|%{python_sitelib}/%{name}|" %{buildroot}%{_unitdir}/%{name}.service
%else
install -d %{buildroot}%{_initddir}
install -p -m 755 %{SOURCE3} %{buildroot}%{_initddir}/%{name}

# Make sure we set proper wrking dir in the sysvinit file
sed -i "s|#WORKDIR#|%{python_sitelib}/%{name}|" %{buildroot}%{_initddir}/%{name}
%endif

cp -r docker_registry test %{buildroot}%{python_sitelib}/%{name}
#cp wsgi.py %{buildroot}%{python_sitelib}/%{name}
cp config/config_sample.yml %{buildroot}%{_sysconfdir}/%{name}.yml

echo "local:
    storage: local
    storage_path: %{_sharedstatedir}/%{name}" >> %{buildroot}%{_sysconfdir}/%{name}.yml

%post
%if %{with systemd}
%systemd_post %{name}.service
%else
/sbin/chkconfig --add %{name}
%endif

%preun
%if %{with systemd}
%systemd_preun %{name}.service
%else
if [ $1 -eq 0 ] ; then
    /sbin/service %{name} stop >/dev/null 2>&1
    /sbin/chkconfig --del %{name}
fi
%endif

%postun
%if %{with systemd}
%systemd_postun_with_restart %{name}.service
%else
if [ "$1" -ge "1" ] ; then
    /sbin/service %{name} condrestart >/dev/null 2>&1 || :
fi
%endif

%files
%dir %{python_sitelib}/%{name}
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%config(noreplace) %{_sysconfdir}/%{name}.yml
%{python_sitelib}/%{name}/docker_registry/*.py
%{python_sitelib}/%{name}/docker_registry/*.pyc
%{python_sitelib}/%{name}/docker_registry/*.pyo
%{python_sitelib}/%{name}/docker_registry/lib/*.py
%{python_sitelib}/%{name}/docker_registry/lib/*.pyc
%{python_sitelib}/%{name}/docker_registry/lib/*.pyo
%{python_sitelib}/%{name}/docker_registry/lib/index/*.py
%{python_sitelib}/%{name}/docker_registry/lib/index/*.pyc
%{python_sitelib}/%{name}/docker_registry/lib/index/*.pyo
%{python_sitelib}/%{name}/docker_registry/storage/*.py
%{python_sitelib}/%{name}/docker_registry/storage/*.pyc
%{python_sitelib}/%{name}/docker_registry/storage/*.pyo
%{python_sitelib}/%{name}/test/*.py
%{python_sitelib}/%{name}/test/*.pyc
%{python_sitelib}/%{name}/test/*.pyo
%{python_sitelib}/%{name}/test/Dockerfile
%{python_sitelib}/%{name}/test/dockertest.sh
%{python_sitelib}/%{name}/test/utils/*.py
%{python_sitelib}/%{name}/test/utils/*.pyc
%{python_sitelib}/%{name}/test/utils/*.pyo
%dir %{_sharedstatedir}/%{name}
%doc LICENSE README.md
%if %{with systemd}
%{_unitdir}/%{name}.service
%else
%{_initddir}/%{name}
%endif

%changelog
* Tue May 06 2014 Lokesh Mandvekar <lsm5@redhat.com> - 0.6.8-8
- import lzma if no backports.lzma

* Fri May 02 2014 Lokesh Mandvekar <lsm5@redhat.com> - 0.6.8-7
- do not complain if redis absent

* Wed Apr 30 2014 Lokesh Mandvekar <lsm5@redhat.com> - 0.6.8-6
- import json if simplejson fails

* Wed Apr 30 2014 Lokesh Mandvekar <lsm5@redhat.com> - 0.6.8-5
- Add python-flask to requires

* Tue Apr 29 2014 Lokesh Mandvekar <lsm5@redhat.com> - 0.6.8-4
- remove python-simplejson runtime requirement

* Tue Apr 29 2014 Lokesh Mandvekar <lsm5@redhat.com> - 0.6.8-3
- remove redis requirement from unitfile

* Wed Apr 23 2014 Lokesh Mandvekar <lsm5@redhat.com> - 0.6.8-2
- M2Crypto branch used: https://github.com/lsm5/docker-registry/tree/m2crypto
- Built for RHEL7

* Fri Apr 18 2014 Marek Goldmann <mgoldman@redhat.com> - 0.6.8-1
- Upstream release 0.6.8

* Mon Apr 07 2014 Marek Goldmann <mgoldman@redhat.com> - 0.6.6-2
- docker-registry settings in /etc/sysconfig/docker-registry not honored,
  RHBZ#1072523

* Thu Mar 20 2014 Marek Goldmann <mgoldman@redhat.com> - 0.6.6-1
- Upstream release 0.6.6
- docker-registry cannot import module jinja2, RHBZ#1077630

* Mon Feb 17 2014 Marek Goldmann <mgoldman@redhat.com> - 0.6.5-1
- Upstream release 0.6.5

* Tue Jan 07 2014 Marek Goldmann <mgoldman@redhat.com> - 0.6.3-1
- Upstream release 0.6.3
- Added python-backports-lzma and python-rsa to R
- Removed configuration file path patch, it's in upstream

* Fri Dec 06 2013 Marek Goldmann <mgoldman@redhat.com> - 0.6.0-4
- Docker-registry does not currently support moving the config file, RHBZ#1038874

* Mon Dec 02 2013 Marek Goldmann <mgoldman@redhat.com> - 0.6.0-3
- EPEL support
- Comments in the sysconfig/docker-registry file

* Wed Nov 27 2013 Marek Goldmann <mgoldman@redhat.com> - 0.6.0-2
- Added license and readme

* Wed Nov 20 2013 Marek Goldmann <mgoldman@redhat.com> - 0.6.0-1
- Initial packaging

