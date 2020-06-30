#! /bin/bash

echo 'source scl_source enable devtoolset-9' >> ~/.bashrc
source scl_source enable devtoolset-9

yum install -y wget rpm-build

wget https://github.com/Takishima/manylinux2014/releases/download/gflags-2.2.2/gflags_$(uname -p).tar.gz
tar zxvf gflags_$(uname -p).tar.gz && rm -f gflags_$(uname -p).tar.gz
rpm -i $(uname -p)/*.rpm && /bin/rm -rf $(uname -p)

/bin/cp -vr . /root/rpmbuild

mkdir -p /root/rpmbuild/SOURCES
echo cd /root/rpmbuild/SOURCES
cd /root/rpmbuild/SOURCES

GLOG_VERSION=0.3.5
if [[ ! -f glog-${GLOG_VERSION}.tar.gz ]]; then
    wget https://github.com/google/glog/archive/v${GLOG_VERSION}.tar.gz -O glog-${GLOG_VERSION}.tar.gz
fi

echo cd /root/rpmbuild/SPECS
cd /root/rpmbuild/SPECS

rpmbuild --define "debug_package %{nil}" \
	 -ba glog.spec

cd /root/rpmbuild/RPMS
tar zcvf glog_$(uname -p).tar.gz $(uname -p)/*
