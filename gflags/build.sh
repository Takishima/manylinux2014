#! /bin/bash

echo 'source scl_source enable devtoolset-9' >> ~/.bashrc
source scl_source enable devtoolset-9

yum install -y wget rpm-build

if [[ $(uname -p) == "x86_64" ]]; then
    yum install -y cmake3
else
    wget https://github.com/Takishima/manylinux2014/releases/download/cmake-3.17.3/cmake3_$(uname -p).tar.gz
    tar zxvf cmake3_$(uname -p).tar.gz && rm -f cmake3_$(uname -p).tar.gz
    rpm -i $(uname -p)/*.rpm && /bin/rm -rf $(uname -p)
fi

alternatives --install /usr/local/bin/cmake cmake /usr/bin/cmake3 20 \
	     --slave /usr/local/bin/ctest ctest /usr/bin/ctest3 \
	     --slave /usr/local/bin/cpack cpack /usr/bin/cpack3 \
	     --slave /usr/local/bin/ccmake ccmake /usr/bin/ccmake3

/bin/cp -vr . /root/rpmbuild

mkdir -p /root/rpmbuild/SOURCES
echo cd /root/rpmbuild/SOURCES
cd /root/rpmbuild/SOURCES
GFLAGS_VERSION=2.2.2

if [[ ! -f gflags-${GFLAGS_VERSION}.tar.gz ]]; then
    wget http://github.com/schuhschuh/gflags/archive/v${GFLAGS_VERSION}/gflags-${GFLAGS_VERSION}.tar.gz
fi

echo cd /root/rpmbuild/SPECS
cd /root/rpmbuild/SPECS

rpmbuild --define "debug_package %{nil}" \
	 -ba gflags.spec

cd /root/rpmbuild/RPMS
tar zcvf gflags_$(uname -p).tar.gz $(uname -p)/*
