Remote Programs
===============

This file documents which programs on the remote host are used to
collect different groups of facts. **bold** is used for executables
that are not standard Unix programs (i.e. not grep, sed, etc.). In
addition to the programs below, we depend on standard shell facilities
like those provided by bash.

- brms.*
  - find
  - sed
  - sort
  - grep / egrep
- cpu.*
  - cat
  - grep
  - sed
  - wc
  - **/usr/sbin/dmidecode**
- date.*
  - date
  - ls
  - grep / egrep
  - **tune2fs**
  - mount
  - sed
  - **yum**
  - tail
- dmi.*
  - **/usr/sbin/dmidecode**
  - grep
  - sed
- etc_release.*
  - cat
  - uname
- file_contents.*
  - cat
- jboss.fuse.*
  - find
  - sed
  - sort
  - echo
- jboss.eap.*
  - **chkconfig (used if present)**
  - find
  - grep / egrep
  - **java**
  - sed
  - stat
  - df
  - tail
  - locate
  - ls
  - sort
  - id
  - test
  - ps
  - **rpm**
  - **systemctl (used if present)**
  - xargs
- redhat_packages
  - **rpm**
- redhat_release.*
  - **rpm**
- subman.*
  - **subscription-manager**
  - grep
  - sed
  - ls
  - wc
  - awk
- uname.*
  - uname
- virt.*
  - command
  - **virsh**
  - ps
  - grep
  - wc
  - **/usr/sbin/dmidecode**
  - sed
  - cat
- virt_what.*
  - command
  - **virt-what**
  - echo
