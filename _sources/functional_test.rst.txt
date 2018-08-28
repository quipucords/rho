Functional Testing
==================

The nature of ``rho`` tool is to discover and scan remote systems. In order
to test this feature locally we need to employ tools to allow us to simulate
a remote environment. We will be utilizing
`Vagrant <https://www.vagrantup.com/>`_ and
`Virtual Box <https://www.virtualbox.org/wiki/VirtualBox>`_ along with Ansible
to create and initialize several virtual systems.

Installing Dependencies
-----------------------

*Virtual Box*

For OS X you can go to the `Virtualbox downloads
<https://www.virtualbox.org/wiki/Downloads>`_ page and installation using the
DMG image.

For Fedora or RHEL systems:
Add the `repo file <http://download.virtualbox.org/virtualbox/rpm/fedora/virtualbox.repo>`_
to /etc/yum.repos.d, then run::

  sudo yum install VirtualBox-5.1


In order to configure VirtualBox run the following commands::

  sudo yum install kernel-devel
  sudo /sbin/vboxconfig

The first command installs the Linux kernel development headers, and the
second tells VirtualBox to build the custom kernel module that it uses.


*Vagrant*

For OS X you can go to the `Vagrant downloads
<https://www.vagrantup.com/downloads.html>`_ page and installation using the
DMG image.

For Fedora or RHEL systems:
Go to `www.vagrantup.com <www.vagrantup.com>`_, click on "Download", and get
the Centos 64-bit RPM. Then install with::

  rpm -ivh <package>.rpm


Provisioning Virtual Systems
----------------------------

From the root directory of the local repository you will see a file named
`Vagrantfile` which specifies three systems that will be setup and initialized
using Ansible. The playbook to be used by Ansible exists in the `vagrant`
directory. Run the following command to provision the systems::

  vagrant up


Note: testing on RHEL
---------------------

The Vagrantfile assumes the existance of a Vagrant box called
`rhel-server-7-1`. You can make a RHEL box by following one of the
many tutorials, such as
https://developers.redhat.com/blog/2016/06/06/using-vagrant-to-get-started-with-rhel/
.

If you don't want to test with RHEL, you can replace that box name
with a different one, such as `centos/7`.

Executing rho on Test Bed
-------------------------

You should have three virtual systems running with the following IP Address:
- 192.168.50.10
- 192.168.50.11
- 192.168.50.12

As part of the Ansible configuration your `id_rsa.pub` file should have been
copied to these machines enabling you to ssh to them locally using the
`vagrant` user. Feel free to try it out with the following::

  ssh vagrant@192.168.50.10

Once you have confirmed connection to your test bed you can run the following
commands to execute a scan using `rho`::

  rho auth add --name=test --username=vagrant --sshkeyfile=~/.ssh/id_rsa
  rho profile add --name=all_test --hosts 192.168.50.[10:12] --auth test
  rho scan --profile=all_test --reportfile=out.csv

Note you create the auth with your private key that matches the public key on
the test machine.
You should be able to view the output of the scan in your local directory.
