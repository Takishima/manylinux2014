#! /bin/bash

# ==============================================================================

_pycall()
{
    PY_ROOT=$1
    shift
    PATH=$PY_ROOT/bin:$PATH "$@"
}

_pyversion()
{
    _pycall "$1" "$2" -c 'import sys; print("%i.%i" % (sys.version_info.major, sys.version_info.minor))'
}

# ==============================================================================

echo 'source scl_source enable devtoolset-9' >> ~/.bashrc
source scl_source enable devtoolset-9

yum install -y git wget rpm-build
yum install -y openmpi-devel gcc-c++ xz-devel bzip2-devel zlib-devel libicu-devel

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
	     --slave /usr/local/bin/ccmake ccmake /usr/bin/ccmake3 \
	     --family cmake

. /usr/share/Modules/init/sh
module load mpi

_tmp=""
pyver_list=""
for py_root in /opt/python/cp3*; do
    _pycall "$py_root" python3 -m pip install numpy
    echo $(_pycall "$py_root" python3 --version)
    PY3_VERSION="$(_pyversion "$py_root" python3)"
    pyver_list="${pyver_list},$PY3_VERSION"
    abiflags="$(_pycall "$py_root" python3-config --abiflags)"
    py_prefix="$(_pycall "$py_root" python3-config --prefix)"

    _tmp="$_tmp\nusing python : ${PY3_VERSION:+$PY3_VERSION }: "
    _tmp="$_tmp${PY3_VERSION:+${py_prefix}/bin/python3 }: "
    _tmp="$_tmp${PY3_VERSION:+${py_prefix}/include/python${PY3_VERSION}${abiflags} }: "
    _tmp="$_tmp${PY3_VERSION:+${py_prefix}/lib };"
done
python_user_config=$_tmp
pyver_list=${pyver_list/,}

sed -e "s/PYTHON_VERSION_LIST/$pyver_list/" -e "s|PYTHON_USER_CONFIG_JAM|$python_user_config|" SPECS/boost.spec.in > SPECS/boost.spec

/bin/cp -vr . /root/rpmbuild

echo cd /root/rpmbuild/SOURCES
cd /root/rpmbuild/SOURCES
BOOST_VERSION=1.73.0
if [[ ! -f boost_${BOOST_VERSION//./_}.tar.bz2 ]]; then
    wget https://sourceforge.net/projects/boost/files/boost/${BOOST_VERSION}/boost_${BOOST_VERSION//./_}.tar.bz2
fi

echo cd /root/rpmbuild/SPECS
cd /root/rpmbuild/SPECS

rpmbuild --without mpich -ba boost.spec

cd /root/rpmbuild/RPMS
tar zcvf boost173_$(uname -p).tar.gz $(uname -p)/*
