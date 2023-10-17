#
# Dockerfile - docker build script for a standard GlueX sim-recon 
#              container image based on alma linux 9.
#
# author: richard.t.jones at uconn.edu
# version: october 17 2023
#
# usage: [as root] $ docker build Dockerfile .
#

FROM docker.io/almalinux:9

# install a few utility rpms
RUN dnf -y update
RUN dnf -y install epel-release
RUN dnf -y install dnf-plugins-core
RUN dnf -y install subversion cmake make imake python3-scons patch git
RUN dnf -y install libtool which bc nano nmap-ncat xterm emacs gdb wget
RUN dnf -y install gcc-c++ gcc-gfortran boost-devel gdb-gdbserver
RUN dnf -y install bind-utils blas blas-devel dump file tcsh expat-devel
RUN dnf -y install libXt-devel openmotif-devel libXpm-devel bzip2-devel
RUN dnf -y install perl-XML-Simple perl-XML-Writer perl-File-Slurp
RUN dnf -y install mesa-libGLU-devel gsl-devel python3-future python3-devel
RUN dnf -y install xrootd-client-libs xrootd-client libXi-devel neon
RUN dnf -y install mariadb mariadb-devel python3-mysqlclient python3-psycopg2
RUN dnf -y install fmt-devel libtirpc-devel atlas rsync
RUN dnf -y install gfal2-all gfal2-devel gfal2-plugin-dcap gfal2-plugin-gridftp gfal2-plugin-srm
RUN dnf -y install hdf5 hdf5-devel pakchois perl-Test-Harness
RUN dnf -y install java-1.8.0-openjdk java-1.8.0-openjdk-devel java-11-openjdk-devel
RUN dnf -y install java-17-openjdk-devel java-latest-openjdk-devel java-hdf5 java-runtime-decompiler
RUN dnf -y install lapack lapack-devel openmpi openmpi-devel
RUN dnf -y install openssh-server postgresql-server-devel postgresql-upgrade-devel
RUN dnf -y install procps-ng strace ucx valgrind
RUN dnf -y install qt5 qt5-x11extras qt5-devel

# install the osg worker node client packages
#RUN rpm -Uvh https://repo.opensciencegrid.org/osg/3.4/osg-3.4-el7-release-latest.rpm
#RUN dnf -y install osg-wn-client
#RUN dnf -y install gfal2-plugin-lfc gfal2-plugin-rfio
#RUN dnf -y install python3-h5py python3-scipy python3-tqdm

# install some dcache client tools
#RUN wget --no-check-certificate https://zeus.phys.uconn.edu/halld/gridwork/dcache-srmclient-3.0.11-1.noarch.rpm
#RUN rpm -Uvh dcache-srmclient-3.0.11-1.noarch.rpm
#RUN rm dcache-srmclient-3.0.11-1.noarch.rpm

# install some python modules
#RUN pip install pandas
#RUN pip install h5hea
#RUN pip install keras
#RUN pip install tensorflow tensorflow-decision-forests

# create custom points, symlinks for gluex software
#RUN wget --no-check-certificate https://zeus.phys.uconn.edu/halld/gridwork/localtest.tar.gz
#RUN tar xf localtest.tar.gz -C /
#RUN rm localtest.tar.gz

# make the cvmfs filesystem visible inside the container
VOLUME /cvmfs/oasis.opensciencegrid.org
