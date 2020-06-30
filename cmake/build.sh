#! /bin/bash


echo 'source scl_source enable devtoolset-9' >> ~/.bashrc
source scl_source enable devtoolset-9

yum install -y wget rpm-build
yum install -y gcc-c++ zlib-devel ncurses-devel openssl-devel

/bin/cp -vr . /root/rpmbuild

echo cd /root/rpmbuild/SOURCES
cd /root/rpmbuild/SOURCES
CMAKE_VERSION=3.17.3
if [[ ! -f cmake-${CMAKE_VERSION}.tar.gz ]]; then
    wget https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/cmake-${CMAKE_VERSION}.tar.gz
fi

echo cd /root/rpmbuild/SPECS
cd /root/rpmbuild/SPECS

rpmbuild --define "debug_package %{nil}" \
	 --with bootstrap \
	 --without test \
	 --without debug \
	 -ba cmake.spec

cd /root/rpmbuild/RPMS
tar zcvf cmake3_$(uname -p).tar.gz $(uname -p)/*
