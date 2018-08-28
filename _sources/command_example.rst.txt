Example rho Scan
=================

Following is the results of an example rho scan. This is the example of the
profile called 'big_test' and it's host auth mapping utilizing the cached
connection data. This is for the scan performed on Wed Aug 10 23:33:17 2016.
Below you will find the example contents for:

- Host Auth Mapping
- Output

The following files are created but are encrypted using the rho vault password provided:

- Inventory
- Scan Profile
- Scan Auths



Example Host Auth Mapping
-------------------------

::

   Wed Aug 10 23:33:17 2016
   -------------------------------
   192.168.124.153
   ----------------------
   seven, root, ********, empty
   eight, t_4, ********, empty


   192.168.124.162
   ----------------------
   two, t_2, ********, empty


   192.168.124.174
   ----------------------
   one, root, ********, empty
   five, root, ********, empty
   seven, root, ********, empty


   192.168.124.15
   ----------------------
   five, root, ********, empty
   seven, root, ********, empty


   192.168.121.007
   ----------------------
   six, vagrant, ********, empty



Facts
-----
The facts collected were:

- uname.hostname
- uname.os
- date.date
- cpu.bogomips
- cpu.vendor_id
- redhat-release.name
- redhat-packages.num_installed_packages

Example Output
--------------

::

   cpu.bogomips,cpu.vendor_id,date.date,redhat-packages.num_installed_packages,redhat-release.name,uname.hostname,uname.os
   5587.07,GenuineIntel,Thu Aug 11 14:55:46 EDT 2016,324,redhat-release-server,localhost.localdomain,Linux
   5587.07,GenuineIntel,Thu Aug 11 14:55:46 EDT 2016,328,redhat-release-server,localhost.localdomain,Linux
   5587.07,GenuineIntel,Thu Aug 11 14:55:46 EDT 2016,324,redhat-release-server,localhost.localdomain,Linux
   5587.07,GenuineIntel,Thu Aug 11 14:55:46 EDT 2016,324,redhat-release-server,localhost.localdomain,Linux
   5587.07,GenuineIntel,Thu Aug 11 14:55:46 EDT 2016,379,centos-release,rho-dev.example.com,Linux
