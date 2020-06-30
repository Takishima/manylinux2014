# Run tests
%bcond_without test

# Verbose test?
%bcond_without debug

# Place rpm-macros into proper location
%global rpm_macros_dir %(d=%{_rpmconfigdir}/macros.d; [ -d $d ] || d=%{_sysconfdir}/rpm; echo $d)

# Setup _pkgdocdir if not defined already
%{!?_pkgdocdir:%global _pkgdocdir %{_docdir}/%{name}-%{version}}

%global major_version 3
%global minor_version 17
# Set to RC version if building RC, else %%{nil}
%global rcver %{nil}

# Uncomment if building for EPEL
%global name_suffix %{major_version}
%global orig_name cmake

Name:           %{orig_name}%{?name_suffix}
Version:        %{major_version}.%{minor_version}.3
Release:        2%{?dist}
Summary:        Cross-platform make system

# most sources are BSD
# Source/CursesDialog/form/ a bunch is MIT
# Source/kwsys/MD5.c is zlib
# some GPL-licensed bison-generated files, which all include an
# exception granting redistribution under terms of your choice
License:        BSD and MIT and zlib
URL:            http://www.cmake.org
Source0:        https://github.com/Kitware/CMake/archive/v%{version}/cmake-%{version}%{?rcver:%rcver}.tar.gz
Source1:        %{name}-init.el
Source2:        macros.%{name}
# See https://bugzilla.redhat.com/show_bug.cgi?id=1202899
Source3:        %{name}.attr
Source4:        %{name}.prov

# Patch to fix RindRuby vendor settings
# http://public.kitware.com/Bug/view.php?id=12965
# https://bugzilla.redhat.com/show_bug.cgi?id=822796
Patch2:         %{name}-findruby.patch
# replace release flag -O3 with -O2 for fedora
Patch3:         %{name}-fedora-flag_release.patch

# Patch for renaming on EPEL
%if 0%{?name_suffix:1}
Patch1000:      %{name}-rename.patch
%endif

BuildRequires: gcc-c++
BuildRequires: ncurses-devel
BuildRequires: zlib-devel
BuildRequires: openssl-devel

Requires:      %{name}-data = %{version}-%{release}
Requires:      rpm

# Source/kwsys/MD5.c
# see https://fedoraproject.org/wiki/Packaging:No_Bundled_Libraries
Provides: bundled(md5-deutsch)

# https://fedorahosted.org/fpc/ticket/555
Provides: bundled(kwsys)

Provides: bundled(libarchive) = 0:3.3.3
Provides: bundled(json-cpp) = 0:1.8.2

# cannot do this in epel, ends up replacing os-provided cmake -- Rex
%if 0%{?fedora}
%{?name_suffix:Provides: %{orig_name} = %{version}}
%endif

%description
CMake is used to control the software compilation process using simple
platform and compiler independent configuration files. CMake generates
native makefiles and workspaces that can be used in the compiler
environment of your choice. CMake is quite sophisticated: it is possible
to support complex environments requiring system configuration, preprocessor
generation, code generation, and template instantiation.


BuildArch:      noarch

%package        data
Summary:        Common data-files for %{name}
Requires:       %{name} = %{version}-%{release}

%description    data
This package contains common data-files for %{name}.

%prep
%autosetup -N -n cmake-%{version}%{?rcver:%rcver}

# Apply renaming on EPEL before all other patches
%if 0%{?name_suffix:1}
%patch1000 -p1 -b .rename
%endif

# We cannot use backups with patches to Modules as they end up being installed
%patch2 -p1 -b .findruby
%patch3 -p1 -b .fedora-flag

echo 'Start cleaning...'
for i in `find . -type f \( -name "*.orig" \)`; do
 rm -f $i
done
echo 'Cleaning finished.'

tail -n +2 %{SOURCE4} >> %{name}.prov
sed -i -e '1i#!%{__python3}' %{name}.prov

%build
export CC=gcc
export CXX=g++
export CFLAGS="%{optflags}"
export CXXFLAGS="%{optflags} -std=gnu++11"
export LDFLAGS="%{?__global_ldflags}"
mkdir build && pushd build
../bootstrap --prefix=%{_prefix} --datadir=/share/%{name} \
 --docdir=/share/doc/%{name} --mandir=/share/man \
 --parallel=`/usr/bin/getconf _NPROCESSORS_ONLN`

make %{?_smp_mflags} VERBOSE=1
# %make_build VERBOSE=1


%install
make install DESTDIR="%{?buildroot}" -C build
# %make_install -C build

find %{buildroot}%{_datadir}/%{name}/Modules -type f | xargs chmod -x
[ -n "$(find %{buildroot}%{_datadir}/%{name}/Modules -name \*.orig)" ] &&
  echo "Found .orig files in %{_datadir}/%{name}/Modules, rebase patches" &&
  exit 1

# Rename cpack-generators manual
# mv %{buildroot}%{_mandir}/man7/cpack-generators.7 %{buildroot}%{_mandir}/man7/cpack-generators.7

# Install major_version name links
%{!?name_suffix:for f in ccmake cmake cpack ctest; do ln -s $f %{buildroot}%{_bindir}/${f}%{major_version}; done}
# Install bash completion symlinks
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions
for f in %{buildroot}%{_datadir}/%{name}/completions/*
do
  ln -s ../../%{name}/completions/$(basename $f) %{buildroot}%{_datadir}/bash-completion/completions/
done
# Install emacs cmake mode
# mkdir -p %{buildroot}%{_emacs_sitelispdir}/%{name}
# install -p -m 0644 Auxiliary/cmake-mode.el %{buildroot}%{_emacs_sitelispdir}/%{name}/%{name}-mode.el
# %{_emacs_bytecompile} %{buildroot}%{_emacs_sitelispdir}/%{name}/%{name}-mode.el
# mkdir -p %{buildroot}%{_emacs_sitestartdir}
# install -p -m 0644 %SOURCE1 %{buildroot}%{_emacs_sitestartdir}/
# RPM macros
install -p -m0644 -D %{SOURCE2} %{buildroot}%{rpm_macros_dir}/macros.%{name}
sed -i -e "s|@@CMAKE_VERSION@@|%{version}|" -e "s|@@CMAKE_MAJOR_VERSION@@|%{major_version}|" %{buildroot}%{rpm_macros_dir}/macros.%{name}
touch -r %{SOURCE2} %{buildroot}%{rpm_macros_dir}/macros.%{name}
%if 0%{?_rpmconfigdir:1}
# RPM auto provides
install -p -m0644 -D %{SOURCE3} %{buildroot}%{_prefix}/lib/rpm/fileattrs/%{name}.attr
install -p -m0755 -D %{name}.prov %{buildroot}%{_prefix}/lib/rpm/%{name}.prov
%endif
mkdir -p %{buildroot}%{_libdir}/%{name}
# Install copyright files for main package
find Source Utilities -type f -iname copy\* | while read f
do
  fname=$(basename $f)
  dir=$(dirname $f)
  dname=$(basename $dir)
  cp -p $f ./${fname}_${dname}
done
# Cleanup pre-installed documentation
rm -rf %{buildroot}%{_docdir}/%{name}
# Install documentation to _pkgdocdir
mkdir -p %{buildroot}%{_pkgdocdir}
cp -pr %{buildroot}%{_datadir}/%{name}/Help %{buildroot}%{_pkgdocdir}
mv %{buildroot}%{_pkgdocdir}/Help %{buildroot}%{_pkgdocdir}/rst

%if %{with test}
%check
pushd build
# CTestTestUpload require internet access.
# Disable RunCMake.CTestCommandLine bacause of the option "show-only_json-v1" failure, probably caused by not recent 'json-cpp'.
# CPackComponentsForAll-RPM-IgnoreGroup failing wih rpm 4.15 - https://gitlab.kitware.com/cmake/cmake/issues/19983
NO_TEST="CTestTestUpload|RunCMake.CTestCommandLine|Server|RunCMake.CPack_RPM|CPackComponentsForAll-RPM-IgnoreGroup"
# kwsys.testProcess-{4,5} are flaky on s390x.
%ifarch s390x
NO_TEST="$NO_TEST|kwsys.testProcess-4|kwsys.testProcess-5"
%endif
# RunCMake.PrecompileHeaders test uses precompiled file presumably compiled with different compiler
# that one of RHEL8 (GCC-8.3.1). See https://bugzilla.redhat.com/show_bug.cgi?id=1721553#c4
%if 0%{?rhel} && 0%{?rhel} > 7
NO_TEST="$NO_TEST|RunCMake.PrecompileHeaders"
%endif
%if %{with debug}
bin/ctest%{?name_suffix} -VV --debug %{?_smp_mflags} -E "$NO_TEST"
%else
bin/ctest%{?name_suffix} %{?_smp_mflags} --output-on-failure -E "$NO_TEST" 
%endif
popd
%endif

%files
%doc Copyright.txt*
%doc COPYING*
%{_bindir}/c%{name}
%{!?name_suffix:%{_bindir}/c%{name}%{major_version}}
%{_bindir}/%{name}
%{!?name_suffix:%{_bindir}/%{name}%{major_version}}
%{_bindir}/cpack%{?name_suffix}
%{!?name_suffix:%{_bindir}/cpack%{major_version}}
%{_bindir}/ctest%{?name_suffix}
%{!?name_suffix:%{_bindir}/ctest%{major_version}}
%{_libdir}/%{name}/

%files data
%{_datadir}/aclocal/%{name}.m4
%{_datadir}/bash-completion/
%{_datadir}/%{name}/
%{rpm_macros_dir}/macros.%{name}
%if 0%{?_rpmconfigdir:1}
%{_rpmconfigdir}/fileattrs/%{name}.attr
%{_rpmconfigdir}/%{name}.prov
%endif

# %files doc
# # Pickup license-files from main-pkg's license-dir
# # If there's no license-dir they are picked up by %%doc previously
# %{?_licensedir:%doc %{_datadir}/licenses/%{name}*}
# %{_pkgdocdir}/


%changelog
* Thu Jun 11 2020 Antonio Trande <sagitter@fedoraproject.org> - 3.17.3-2
- Change command to add Python shebang of the cmake3.prov file (epel bz#1845614)

* Mon Jun 01 2020 Antonio Trande <sagitter@fedoraproject.org> - 3.17.3-1
- Release 3.17.3

* Wed Apr 29 2020 Antonio Trande <sagitter@fedoraproject.org> - 3.17.2-1
- Release 3.17.2

* Mon Apr 27 2020 Antonio Trande <sagitter@fedoraproject.org> - 3.17.1-2
- Fix macros for bundled libraries
- Add Provides for bundled libraries

* Sun Apr 26 2020 Antonio Trande <sagitter@fedoraproject.org> - 3.17.1-1
- Release 3.17.1
- Drop EPEL6 support
- Add openssl BR
- Fix rhbz#1811358
- Use system zstd

* Sun Mar 08 2020 Antonio Trande <sagitter@fedoraproject.org> - 3.14.7-1
- Bugfix release 3.14.7

* Sun Sep 01 2019 Antonio Trande <sagitter@fedoraproject.org> - 3.14.6-2
- Fix rename patches

* Tue Aug 27 2019 Antonio Trande <sagitter@fedoraproject.org> - 3.14.6-1
- Update to cmake-3.14.6 (rhbz#1746146, rhbz#1746104)
- Do not use system jsoncpp
- Split off appdata file as external source file

* Sat May 25 2019 Antonio Trande <sagitter@fedoraproject.org> - 3.13.5-1
- Update to cmake-3.13.5

* Thu Mar 07 2019 Troy Dawson <tdawson@redhat.com> - 3.13.4-2
- Rebuilt to change main python from 3.4 to 3.6

* Sun Feb 03 2019 Antonio Trande <sagitter@fedoraproject.org> - 3.13.4-1
- Update to cmake-3.13.4

* Sat Jan 19 2019 Antonio Trande <sagitter@fedoraproject.org> - 3.13.3-1
- Update to cmake-3.13.3

* Sat Dec 29 2018 Antonio Trande <sagitter@fedoraproject.org> - 3.13.1-1
- Update to cmake-3.13.1
- Use Python3 on epel7
- Perform all tests

* Thu Oct 04 2018 Antonio Trande <sagitter@fedoraproject.org> - 3.12.2-1
- Update to cmake-3.12.2

* Mon Aug 20 2018 Antonio Trande <sagitter@fedoraproject.org> - 3.12.1-1
- Update to cmake-3.12.1

* Fri Jul 27 2018 Antonio Trande <sagitter@fedoraproject.org> - 3.12.0-1
- Update to cmake-3.12.0
- Use %%_metainfodir

* Sat May 19 2018 Antonio Trande <sagitter@fedoraproject.org> - 3.11.2-1
- Update to cmake-3.11.2
- Fix appdata file's entries

* Sat Apr 07 2018 Antonio Trande <sagitter@fedoraproject.org> - 3.11.0-1
- Update to cmake-3.11.0
- Add libuv rhash development packages
- Adapt 'cmake3-rename' patch to CMake-3.11
- Move appdata file into the metainfo sub-data directory

* Thu Feb 09 2017 Orion Poplawski <orion@cora.nwra.com> 3.6.3-1
- Update to 3.6.3
- Fix cmake3.prov error

* Thu Sep 01 2016 Rex Dieter <rdieter@fedoraproject.org> 3.6.1-2
- drop Provides: cmake

* Tue Aug 23 2016 Björn Esser <fedora@besser82.io> - 3.6.1-1
- Update to 3.6.1 (#1353778)

* Fri Apr 22 2016 Björn Esser <fedora@besser82.io> - 3.5.2-2
- Do not own /usr/lib/rpm/fileattrs

* Sat Apr 16 2016 Björn Esser <fedora@besser82.io> - 3.5.2-1
- Update to 3.5.2 (#1327794)

* Fri Mar 25 2016 Björn Esser <fedora@besser82.io> - 3.5.1-1
- Update to 3.5.1 (#1321198)

* Fri Mar 11 2016 Björn Esser <fedora@besser82.io> - 3.5.0-2.1
- fix emacs-filesystem requires for epel6

* Thu Mar 10 2016 Björn Esser <fedora@besser82.io> - 3.5.0-2
- keep Help-directory and its contents in %%_datadir/%%name

* Wed Mar 09 2016 Björn Esser <fedora@besser82.io> - 3.5.0-1.2
- do not provide cmake = %%{version}

* Wed Mar 09 2016 Björn Esser <fedora@besser82.io> - 3.5.0-1.1
- fix macros

* Wed Mar 09 2016 Björn Esser <fedora@besser82.io> - 3.5.0-1
- update to 3.5.0 final

* Tue Mar 08 2016 Björn Esser <fedora@besser82.io> - 3.5.0-0.3.rc3
- bump after review (#1315193)

* Mon Mar 07 2016 Björn Esser <fedora@besser82.io> - 3.5.0-0.2.rc3
- addressing issues from review (#1315193)
  - fix emacs-packaging
  - use %%license-macro
  - fix arch'ed Requires
  - removed BuildRoot
  - use %%global instead of %%define
  - split documentation into noarch'ed doc-subpkg

* Mon Mar 07 2016 Björn Esser <fedora@besser82.io> - 3.5.0-0.1.rc3
- initial epel-release (#1315193)
