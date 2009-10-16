#
# Copyright (c) 2009 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#

""" Unit tests for CLI """

from rho.clicommands import *

import unittest
import os

class CliCommandsTests(unittest.TestCase):

    def _run_test(self, cmd, args):
        os.environ[RHO_PASSPHRASE] = "blerg"

        sys.argv = args
        cmd.main()

    def test_scan(self):
        self._run_test(ScanCommand(), ["bin/rho", "scan"])

    def test_profile_show(self):
        self._run_test(ProfileShowCommand(), ["bin/rho", "profile", "show"])

    def test_profile_add(self):
        self._run_test(ProfileAddCommand(), ["bin/rho", "profile", "add", "--name", "profilename"])


    def test_auth_show(self):
        self._run_test(AuthShowCommand(), ["bin/rho", "auth", "show"])

    def test_auth_add(self):
        self._run_test(AuthAddCommand(), ["bin/rho", "auth", "add"])

    def test_dumpconfig(self):
        self._run_test(DumpConfigCommand(), ['bin/rho', 'dumpconfig',
            '--encrypted-file', 'test/data/encrypted.data'])
