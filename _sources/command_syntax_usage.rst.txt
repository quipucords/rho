Command Syntax & Usage
======================

The basic syntax is:

``rho command subcommand [options]``

There are four rho commands:
 * ``auth`` - for managing auth entries
 * ``profile`` - for managing profile entries
 * ``scan`` - for running scans
 * ``fact`` - to show information about the facts rho can collect

``auth`` and ``profile`` both have five subcommands:
 * ``add`` - to create a new entry
 * ``edit`` - to modify an existing entry
 * ``clear`` - to remove any or all entries
 * ``show`` - to display a specific entry
 * ``list`` - to display one or more entries

``fact`` has two subcommands:
  * ``list`` - to display the list of facts that can be scanned
  * ``hash`` - to hash sensitive facts within report

The complete list of options for each command and subcommand are listed in the
rho manpage with other usage examples. The common options are listed with the
examples in this document.

Auth Entries
------------

The first step to configuring rho is adding auth credentials to use to connect
over SSH. Each authentication identity requires its own auth entry.

``rho auth add --name=server1creds --username=rho-user --sshkeyfile=/etc/ssh/ssh_host_rsa_key``

*Note:* --password not being passed or passed as empty are considered the same thing.

SSH Key with a Passphrase
^^^^^^^^^^^^^^^^^^^^^^^^^

There are two ways to handle ssh keys with passphrases. If a
passphrase-protected ssh key is specified in an auth and the key is
not present in the ssh agent, then Rho will prompt the user for the
passphrase each time it needs to use the key.

To avoid repetitive prompts, users can add their keys to the local ssh
agent (as documented at
http://docs.ansible.com/ansible/latest/intro_getting_started.html),
which will decrypt them once and make them available to Rho.

Profiles
---------

Then, create the profile to use for the scan. This should include a list of IP
addresses or ranges, and the auth identity to use.

``rho profile add --name=profile1 --hosts 1.2.3.[0:255] --auth server1creds server2creds``

The hosts can be passed in as a file with all the ranges listed in newlines. Example below:

``rho profile edit --name=profile1 --hosts hosts_file --auth server1creds server2creds``

where ``hosts_file`` contains the ip address or ranges separated by newlines::

  1.2.3.1
  1.2.3.14
  1.2.4.34

Scanning
--------

The options required for a scan are the profile to use and the file path for
the report. Optionally we can pass the number of Ansible forks and the facts to
be collected. Finally the ``cache`` option tells rho that the profile you are
providing has already been processed for connection mappings.

``rho scan --profile=profile1 --reportfile=report.csv``

Since rho collects the successful host auth mappings from a full scan
the user doesn't have to worry about iterating through multiple auths and hosts
again and again in the same profile as long as the profile hasn't changed when
utilizing the ``cache`` option. For purposes of record keeping the host
mapping files are always written to whenever a scan is done using a profile.
When profiles are deleted the host auth mappings
corresponding to the profile are renamed with prefix *(DELETED PROFILE)* so that
they are recognizable. Every scan has a timestamp in the mappings.

As far as the auths used by the inventory of a particular scan is concerned, it
is important to note that the order of the auths passed into a profile matters.
A profile by definition takes in one ordering of auths and all the hosts in
the profile are tested in that order with the auths before the first auths to
work are picked to run the fact collection. Therefore, it's up to the user
to pass in auths as per the priority they deem fit for a profile. If a non root
auth is better tried first and then the root auth then the user has to pass in the
auths in the order as ``--auth <nonroot_1> <nonroot_2> <root_1> <root_2>`` etc.

The output of the Ansible process is saved to `$XDG_DATA_HOME/rho/scan_log` by
default, for debugging. This location can be changed with the
`--logfile` flag.

Common Flags
------------

All rho commands accept the `-v` flag, which increases the verbosity
of rho's output. It comes in four varieties: `-v`, `-vv`, `-vvv`, and
`-vvvv`, with more `v`'s indicating more verbose output. The verbose
output can be useful in debugging.

Output
------

The important part about a scan is the results report. By default,
this contains a large amount of information about the operating system, hardware, and platform.

.. include:: ../facts.rst


The output can then be configured to contain any combination of these fields by using the
``--facts`` option. The following is the format rho understands for all the facts. Some or all
of these facts can be requested by either as a CLI list i.e. ``--facts <fact_1> <fact_2>`` etc
or by passing in a file with a new fact on every line in the format as follows. A value
of 'default' will get all the information listed above.

For further details of the command usage view the following
`example <command_example.rst>`_.

Scan User Permissions
---------------------

Some of the output facts will report an error if the user used to perform the
scan does not have the appropriate permissions to execute the command used to
gather the targeted facts. The following set of facts require *admin/root*
permissions to collect the facts:

- ``cpu.socket_count``
- ``date.anaconda_log``
- ``date.yum_history``
- ``dmi.x``
- ``subman.x``
- ``virt.virt``
- ``virt.type``
- ``virt-what.x``

The scan user can successful collect these values if the user is **root** or
has the ability to perform a ``sudo``. The following
provides the necessary content for the ``/etc/sudoers`` file where *scanuser*
represents the username used for the scan.

::

  Cmnd_Alias SCAN = /sbin/subscription-manager, /usr/sbin/dmidecode, /usr/sbin/virt-what
  scanuser ALL=NOPASSWD: SCAN

If the scan user uses a password to sudo, one can be given with the
`--sudo-password` option to the `auth add` and `auth edit`
commands. The sudo-with-password fundtionality can be tested by using
the 'askpass' box in the Vagrantfile.

JBoss Lightweight and Heavyweight Scans
---------------------------------------

The JBoss facts come in two kinds. Some facts attempt to detect JBoss
by looking at the running process table, or at a small list of common
installation paths. These facts are run in rho by default, and can be
selected using `--facts jboss`. They are called the "lightweight
scan".

The other set of facts uses `find` to search the entire filesystem on
the machine being scanned. These are more thorough, because they can
find an EAP installation even if it is in an unusual location and not
running, but they also require much more I/O and computation on the
scanned machine. These are called the "heavyweight scan". They are not
run by default, but can be selected with `--facts all`. There is a
danger that the heavyweight scan could interfere with a user
application running on the scanned machine, especially if that
application uses a lot of CPU or does a lot of I/O.

The distinction is meant to allow a tradeoff between performance and
completeness. A reasonable approach would be to run the lightweight
scan first, see if the results make sense, and decide whether to run
the heavyweight scan on a host-by-host basis.

Programs on Remote Machines
---------------------------

Besides standard Unix utilities, some rho fact collectors depend on
specific programs being installed on the machines being scanned. The
complete list is at `remote programs
<github.com/quipucords/rho/doc/source/remote_programs.rst>`_.
