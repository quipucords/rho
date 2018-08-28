rho
===

Name
----

rho - Discover and manage product entitlement metadata on your network.


Synopsis
--------

``rho command subcommand [options]``

Description
-----------

Rho, and the ``rho`` command, is a network discovery and inspection tool to identify environment data, or *facts*, such as the number of physical and virtual systems on a network, their operating systems and other configuration data, and versions of some key packages and products for almost any Linux or UNIX version. The ability to discover and inspect the software and systems that are running on the network improves your ability to understand and report on your entitlement usage. Ultimately, this discovery and inspection process is part of the larger system administration task of managing your inventories.

Rho uses two types of profiles to manage the discovery and inspection process. An *authentication profile* contains credentials such as the username and password or SSH key of the user that runs the discovery and inspection process.  A *network profile* defines the network, such as a host, subnet, or network that is being monitored, plus includes one or more authentication profiles to use to access that network during the discovery and inspection process. You can save multiple authentication profiles and network profiles to use with Rho in various combinations as you run discovery and inspection processes, or *scans*.

By default, the authentication profiles and network profiles that are created when using Rho are stored in encrypted files. The files are encrypted with AES-256 encryption and are decrypted when the ``rho`` command runs, by using a *vault password* to access the files.

Rho is an *agentless* discovery and inspection tool, so there is no need to install the tool on multiple systems. Discovery and inspection for the entire network is centralized on a single machine.

This man page describes the commands, subcommands, and options for the ``rho`` command and includes basic usage information. For more detailed information and examples, including best practices, see the Rho README file.

Usage
-----

``rho`` performs four major tasks:

* Creating authentication profiles:

  ``rho auth add ...``

* Creating network profiles:

  ``rho profile add --name=X --hosts X Y Z --auth A B``

* Running a scan:

  ``rho scan --profile=X --reportfile=Y``

* Working with facts that are gathered in a scan:

  ``rho fact ...``

The following sections describe these commands, their subcommands, and their options in more detail.

Authentication Profiles
-----------------------

Use the ``rho auth`` command to create and manage authentication profiles.

An authentication profile defines a set of user credentials to be used during a scan. These user credentials include a username and a password or SSH key. Rho uses SSH to connect to servers on the network and uses authentication profiles to obtain the user credentials that are required to access those servers.

When a scan runs, it uses a network profile that contains the host names or IP addresses to be accessed. The network profile also contains references to the authentication profiles that are required to access those systems. A single network profile can contain a reference to multiple authentication profiles as needed to connect to all systems in that network.

Creating and Editing Authentication Profiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create an authentication profile, supply SSH credentials as either a username-password pair or a username-key pair. Rho stores each set of credentials in a separate authentication profile entry.

**rho auth add --name=** *name* **--username=** *username* **(--password | --sshkeyfile=** *key_file* **)** **[--sudo-password]** **[--vault=** *vault_file* **]**

``--name=name``

  Required. Sets the name of the new authentication profile. For the value, use a descriptive name that is meaningful to your organization. For example, you could identify the user or server that the authentication profile relates to, such as ``admin12`` or ``server1_jdoe``. Do not include the password as part of this value, because the value for the ``--name`` option might be logged or printed during ``rho`` execution.

``--username=username``

  Required. Sets the username of the SSH identity that is used to bind to the server.

``--password``

  Prompts for the password for the ``--username`` identity. Mutually exclusive with the ``--sshkeyfile`` option.

``--sshkeyfile=key_file``

  Sets the path of the file that contains the private SSH key for the ``--username`` identity. Mutually exclusive with the ``--password`` option.

``--sudo-password``

  Prompts for the password to be used when running a command that uses sudo on the systems to be scanned.

``--vault=vault_file``

  Contains the path of the file that contains the vault password. The vault password is the password that controls access to the encrypted Rho data such as authentication and network profiles, scan data, and other information. If you do not have a file to use as the value for this option, do not use the option. You are then prompted to enter the vault password or to create a new vault password if one does not exist. At any time, you can save this password in a file such as a text file. You can then use the --vault option in subsequent Rho commands. Because the encrypted Rho data could contain sensitive information, make sure that this vault password file is stored in a location that has limited access.

The information in an authentication profile, such as a password, sudo password, SSH keys, or even the username, might change. For example, network security might require passwords to be updated every few months. Use the ``rho auth edit`` command to change the SSH credential information in an authentication profile. The parameters for ``rho auth edit`` are the same as those for ``rho auth add``.

**rho auth edit --name=** *name* **--username=** *username* **(--password | --sshkeyfile=** *key_file* **)** **[--sudo-password]** **[--vault=** *vault_file* **]**

Listing and Showing Authentication Profiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``rho auth list`` command returns the details for every authentication profile that is configured for Rho. This output includes the name, username, password, SSH keyfile and sudo password for each entry. Passwords are masked if provided, if not, they will appear as ``null``.

**rho auth list [--vault=** *vault_file* **]**

``--vault=vault_file``

  Contains the path of the file that contains the vault password. Because the encrypted Rho data could contain sensitive information, make sure that this vault password file is stored in a location that has limited access.

The ``rho auth show`` command is the same as the ``rho auth list`` command, except that it returns details for a single specified authentication profile.

**rho auth show --name=** *name* **[--vault=** *vault_file* **]**

``--name=name``

  Required. Contains the authentication profile entry to display.

``--vault=vault_file``

  Contains the path of the file that contains the vault password. Because the encrypted Rho data could contain sensitive information, make sure that this vault password file is stored in a location that has limited access.

Clearing Authentication Profiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As the network infrastructure changes, it might be necessary to delete some authentication profiles. Use the ``clear`` subcommand to delete authentication profiles.

**IMPORTANT:** Remove or change the authentication profile from any network profile that uses it *before* clearing an authentication profile. Otherwise, any attempt to use the network profile to run a scan runs the command with a nonexistent authentication profile, an action that causes the ``rho`` command to fail.

**rho auth clear (--name** *name* **| --all) [--vault=** *vault_file* **]**

``--name=name``

  Contains the authentication profile to clear. Mutually exclusive with the ``--all`` option.

``--all``

  Clears all stored authentication profiles. Mutually exclusive with the ``--name`` option.

``--vault=vault_file``

  Contains the path of the file that contains the vault password. Because the encrypted Rho data could contain sensitive information, make sure that this vault password file is stored in a location that has limited access.

Network Profiles
----------------

Use the ``rho profile`` command to create and manage network profiles.

A network profile defines a collection of network information, including IP addresses or host names, SSH ports, and SSH credentials. The SSH credentials are provided through reference to one or more authentication profiles. A discovery and inspection scan can reference a network profile so that the act of running the scan is automatic and repeatable, without a requirement to reenter network information for each scan attempt.

Creating and Editing Network Profiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a network profile, supply one or more host names or IP addresses to connect to with the ``--hosts`` option and the authentication profiles needed to access those systems with the ``--auth`` option. The ``rho profile`` command allows multiple entries for each of these options. Therefore, a single network profile can access a collection of servers and subnets as needed to create an accurate and complete scan.

**rho profile add --name=** *name* **--hosts** *ip_address* **--auth** *auth_profile* **[--sshport=** *ssh_port* **] [--vault=** *vault_file* **]**

``--name=name``

  Required. Sets the name of the new network profile. For the value, use a descriptive name that is meaningful to your organization, such as ``APSubnet`` or ``Lab3``.

``--hosts ip_address``

  Sets the host name, IP address, or IP address range to use when running a scan. You can also provide a path for a file that contains a list of host names or IP addresses or ranges, where each item is on a separate line. The following examples show several different formats that are allowed as values for the ``--hosts`` option:

  * A specific host name:

    --hosts server.example.com

  * A specific IP address:

    --hosts 192.0.2.19

  * An IP address range:

    --hosts 192.0.2.[0:255]
    or
    --hosts 192.0.2.0/24

  * A file:

    --hosts /home/user1/hosts_file

``--auth auth_profile``

  Contains the name of the authentication profile to use to authenticate to the systems that are being scanned. If the individual systems that are being scanned each require different authentication credentials, you can use more than one authentication profile. To add multiple authentication profiles to the network profile, separate each value with a space, for example:

  ``--auth first_auth second_auth``

  **IMPORTANT:** An authentication profile must exist before you attempt to use it in a network profile.

``--sshport=ssh_port``

  Sets a port to be used for the scan. This value supports discovery and inspection on a non-standard port. By default, the scan runs on port 22.

``--vault=vault_file``

  Contains the path of the file that contains the vault password. Because the encrypted Rho data could contain sensitive information, make sure that this vault password file is stored in a location that has limited access.

The information in a network profile might change as the structure of the network changes. Use the ``rho profile edit`` command to edit a network profile to accommodate those changes.

Although ``rho profile`` options can accept more than one value, the ``rho profile edit`` command is not additive. To edit a network profile and add a new value for an option, you must enter both the current and the new values for that option. Include only the options that you want to change in the ``rho profile edit`` command. Options that are not included are not changed.

**rho profile edit --name** *name* **[--hosts** *ip_address* **] [--auth** *auth_profile* **] [--sshport=** *ssh_port* **] [--vault=** *vault_file* **]**

For example, if a network profile contains a value of ``server1creds`` for the ``--auth`` option, and you want to change that network profile to use both the ``server1creds`` and ``server2creds`` authentication profiles, you would edit the network profile as follows:

``rho profile edit --name=myprofile --auth server1creds server2creds``

**TIP:** After editing a network profile, use the ``rho profile show`` command to review those edits.

Listing and Showing Network Profiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``rho profile list`` command returns the details for all configured network profiles. The output of this command includes the host names, IP addresses, or IP ranges, the authentication profiles, and the ports that are configured for each network profile.

**rho profile list [--vault=** *vault_file* **]**

``--vault=vault_file``

  Contains the path of the file that contains the vault password. Because the encrypted Rho data could contain sensitive information, make sure that this vault password file is stored in a location that has limited access.

The ``rho profile show`` command is the same as the ``rho profile list`` command, except that it returns details for a single specified network profile.

**rho profile show --name=** *profile* **[--vault=** *vault_file* **]**

``--name=profile``

  Required. Contains the network profile to display.

``--vault=vault_file``

  Contains the path of the file that contains the vault password. Because the encrypted Rho data could contain sensitive information, make sure that this vault password file is stored in a location that has limited access.

Clearing Network Profiles
~~~~~~~~~~~~~~~~~~~~~~~~~

As the network infrastructure changes, it might be necessary to delete some network profiles. Use the ``rho profile clear`` command to delete network profiles.

**rho profile clear (--name=** *name* **| --all) [--vault=** *vault_file* **]**

``--name=name``

  Contains the network profile to clear. Mutually exclusive with the ``--all`` option.

``--all``

  Clears all stored network profiles. Mutually exclusive with the ``--name`` option.


``--vault=vault_file``

  Contains the path of the file that contains the vault password. Because the encrypted Rho data could contain sensitive information, make sure that this vault password file is stored in a location that has limited access.

Facts
-----

Use the ``rho fact`` command to view information that can be reported in a scan or to alter the contents of a report that is created from the ``rho scan`` command.

Listing Facts
~~~~~~~~~~~~~

To generate a list of facts that can be gathered during the discovery and inspection scanning process, use the ``rho fact list`` command.

**rho fact list [--filter=** *reg_ex* **]**

``--filter=reg_ex``

  Optional. Contains a regular expression to use to provide a filtered view of the list of facts. For example, the ``uname.*`` string returns only those facts that contain that string in the fact name.

Hashing Facts
~~~~~~~~~~~~~

To encrypt sensitive facts within the comma separated values (CSV) file output of a scan, use the ``rho fact hash`` command. The sensitive facts that are hashed with this command are *connection.host, connection.port, uname.all,* and *uname.hostname.*

**rho fact hash --reportfile=** *file* **[--outputfile=** *path* **]**

``--reportfile=file``

  Contains the path of the comma-separated values (CSV) report file to read as input.

``--outputfile=path``

  Contains the path of the comma-separated values (CSV) report file to be written as output. Creates a new report with the sensitive facts encrypted.

Scanning
--------

Use the ``rho scan`` command to run discovery and inspection scans on the network. This command scans all of the host names or IP addresses that are defined in the supplied network profile, and then writes the report information to a comma separated values (CSV) file. Note: Any ssh-agent connection setup for a target host '
              'will be used as a fallback if it exists.

**rho scan --profile=** *profile_name* **--reportfile=** *file* **[--facts** *file or list of facts* **] [--scan-dirs=** *file or list of remote directories* **] [--cache] [--vault=** *vault_file* **] [--logfile=** *log_file* **] [--ansible-forks=** *num_forks* **]**

``--profile=profile_name``

  Contains the name of the network profile to use to run the scan.

``--reportfile=file``

  Sets the path of the report file to create from the scan output. This file is saved in the comma-separated values (CSV) format.

``--facts fact1 fact2``

  Contains the list of facts that are returned in the scan report. You can provide multiple values for this option, with each value separated by a space, or provide a path to a file that contains a list of facts, where each fact is on a separate line. The list below is included as an example and is not exhaustive. Use the ``rho fact list`` command to get the full list of available facts.


-  cpu.count: number of processors
-  cpu.cpu_family: cpu family
-  cpu.model_name: cpu model name
-  cpu.vendor_id: cpu vendor name
-  dmi.bios-vendor: bios vendor name
-  etc-release.etc-release: contents of /etc/release (or equivalent)
-  instnum.instnum: installation number
-  connection.uuid: unique id associate with scan
-  connection.ip: ip address
-  connection.port: ssh port
-  redhat-release.name: name of package that provides 'redhat-release'
-  redhat-release.release: release of package that provides 'redhat-release'
-  redhat-release.version: version of package that provides 'redhat-release'
-  systemid.system_id: Red Hat Network system id
-  systemid.username: Red Hat Network username
-  virt.virt: host, guest, or baremetal
-  virt.type: type of virtual system
-  uname.all: uname -a (all)
-  uname.hardware_platform: uname -i (hardware_platform)
-  uname.hostname: uname -n (hostname)
-  uname.kernel: uname -r (kernel)
-  uname.os: uname -s (os)
-  uname.processor: uname -p (processor)

``--scan-dirs dir1 dir2``

  Contains the list of directories on remote systems to scan for products. This option is intended to help scope a scan for systems with a very large file system under the root directory. You can provide multiple values for this option, with each value separated by a space, or provide a path to a file that contains a list of directories, where each directory is on a separate line.

``--cache``

  Restricts the scope of the scan to the hosts that were discovered in the previous scan. Use this option to discover software on hosts that were discovered in a previous scan. Do not use this option to scan for new hosts.

``--vault=vault_file``

  Contains the path of the file that contains the vault password. Because the encrypted Rho data could contain sensitive information, make sure that this vault password file is stored in a location that has limited access.

``--logfile=log_file``

  Contains the path of the log file for this instance of the ``rho scan`` command.

``--ansible-forks=num_forks``

  Sets the number of systems to scan in parallel. The default number is 50 concurrent connections.

Options for All Commands
------------------------

The following options are available for every Rho command.

``--help``

  Prints the help for the ``rho`` command or subcommand.

``-v``

  Enables the verbose mode. The ``-vvv`` option increases verbosity to show more information. The ``-vvvv`` option enables connection debugging.

Examples
--------

:Creating a new authentication profile with a keyfile: ``rho auth add --name=new-creds --username=rho-user --sshkeyfile=/etc/ssh/ssh_host_rsa_key``
:Creating a new authentication profile with a password: ``rho auth add --name=other-creds --username=rho-user-pass --password``
:Creating a new profile: ``rho profile add --name=new-profile --hosts 1.192.0.19 --auth new-creds``
:Editing a profile: ``rho profile edit --name=new-profile --hosts 1.192.0.[0:255] --auth new-creds other-creds``
:Running a scan with a profile: ``rho scan --profile=new-profile --reportfile=/home/jsmith/Desktop/output.csv``

Security Considerations
-----------------------

The authentication profile credentials that are used to access servers are stored with the network profile configuration in an AES-256 encrypted configuration file. A vault password is used to access this file. The vault password and decrypted file contents are in the system memory, and could theoretically be written to disk if memory swapping is enabled.

Although you can run the ``rho`` command without prompts (such as scheduling a cron job) by using a file to pass the vault password, the use of a file for vault password storage is not without risk; therefore, its use requires caution. The vault password allows access to encrypted Rho data that could contain sensitive information. Make sure that this vault password file, if used, is stored in a location that has limited access.

Authors
-------

The rho tool was originally written by Adrian Likins <alikins-at-redhat.com>, Devan Goodwin <dgoodwin-at-redhat.com>, Jesus M. Rodriguez <jesusr-at-redhat.com>, and Chris Snyder <csnyder@redhat.com> of Red Hat, Inc.
rho has been continued to be enhanced by Karthik Harihar Reddy Battula <karthikhhr@gmail.com>, Chris Hambridge <chambrid@redhat.com>, and Noah Lavine <nlavine@redhat.com>.

Copyright
---------

(c) 2017 Red Hat, Inc. Licensed under the GNU Public License version 2.
