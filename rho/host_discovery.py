# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Discover hosts on a network."""

from __future__ import print_function
from collections import defaultdict
import os
import re
from ansible.parsing.utils.addresses import parse_address
from ansible.plugins.inventory import detect_range, expand_hostname_range
from rho import ansible_utils
from rho.translation import _
from rho.utilities import (log, PING_INVENTORY_PATH,
                           PING_LOG_PATH,
                           process_discovery_scan)

DEFAULT_DISCOVERY_TIMEOUT = 20


def process_ping_output(out_lines):
    """Find successful hosts from the output of a ping command.

    Use this function by using ansible to run echo "Hello" on remote
    hosts, then sending the output to this function.

    :param out_lines: an iterator returning lines of Ansible output.
    :returns: the hosts that pinged successfully, as a set and those that
        failed, as a set.
    """

    success_hosts = set()
    failed_hosts = set()
    unreachable_hosts = set()

    # Ansible output has the format
    # host | UNREACHABLE! => {
    #     "changed": false,
    #     "msg": "Failed to connect to the host via ssh ...",
    #     "unreachable": true
    #    }
    #   hostname | SUCCESS | rc=0 >>
    #   Hello
    # with the above two lines repeated for each host
    for line in out_lines:
        ansi_escape = re.compile(r'\x1b[^m]*m')
        line = ansi_escape.sub('', line)
        pieces = line.split('|')
        if len(pieces) == 3 and pieces[1].strip() == 'SUCCESS':
            success_hosts.add(pieces[0].strip())
        elif len(pieces) == 3 and pieces[1].strip() == 'FAILED':
            failed_hosts.add(pieces[0].strip())
        elif len(pieces) == 2 and pieces[1].strip().startswith('UNREACHABLE'):
            unreachable_hosts.add(pieces[0].strip())

    log.info('Ping log reached hosts: %s', success_hosts)
    log.info('Ping log failed hosts: %s', failed_hosts)
    log.info('Ping log unreachable hosts: %s', unreachable_hosts)

    return success_hosts, failed_hosts, unreachable_hosts


def _expand_hostpattern(hostpattern):
    """Expands pattern into list of hosts.

    Takes a single host pattern and returns a list of hostnames.
    :param hostpattern: a single host pattern
    :returns: list of hostnames
    """
    # Can the given hostpattern be parsed as a host with an optional port
    # specification?

    try:
        # pylint: disable=unused-variable
        (pattern, port) = parse_address(hostpattern, allow_ranges=True)
    except:  # noqa pylint: disable=bare-except
        # not a recognizable host pattern
        pattern = hostpattern

    # Once we have separated the pattern, we expand it into list of one or
    # more hostnames, depending on whether it contains any [x:y] ranges.

    if detect_range(pattern):
        hostnames = expand_hostname_range(pattern)
    else:
        hostnames = [pattern]

    return hostnames


# Creates the inventory for pinging all hosts and records
# successful auths and the hosts they worked on
# pylint: disable=too-many-statements, too-many-arguments, unused-argument
def create_ping_inventory(vault, vault_pass, profile_ranges, profile_port,
                          credential, forks, ansible_verbosity):

    """Find which auths work with which hosts.

    :param vault: a Vault object
    :param vault_pass: password for the Vault?
    :param profile_ranges: hosts for the profile
    :param profile_port: the SSH port to use
    :param credential: auth to use
    :param forks: the number of Ansible forks to use

    :returns: a tuple of
      (list of IP addresses that worked for any auth,
       map from host IPs to SSH ports that worked with them,
       map from host IPs to lists of auths that worked with them
      )
    """

    # pylint: disable=too-many-locals
    all_hosts = []
    success_hosts = set()
    failed_hosts = set()
    unreachable_hosts = set()
    success_port_map = defaultdict()
    success_auth_map = defaultdict(list)
    hosts_dict = {}

    for profile_range in profile_ranges:
        hosts = _expand_hostpattern(profile_range)
        all_hosts += hosts

    for host in all_hosts:
        hosts_dict[host] = {'ansible_host': host,
                            'ansible_port': profile_port}

    vars_dict = ansible_utils.auth_as_ansible_host_vars(credential)

    yml_dict = {'alpha': {'hosts': hosts_dict, 'vars': vars_dict}}
    vault.dump_as_yaml_to_file(yml_dict, PING_INVENTORY_PATH)
    ansible_utils.log_yaml_inventory('Ping inventory', yml_dict)

    total_hosts_count = len(all_hosts)
    rho_discovery_timeout = os.getenv(
        'RHO_DISCOVERY_TIMEOUT', DEFAULT_DISCOVERY_TIMEOUT)

    try:
        rho_discovery_timeout = int(rho_discovery_timeout)
    except ValueError:
        rho_discovery_timeout = DEFAULT_DISCOVERY_TIMEOUT

    discovery_timeout = ((total_hosts_count // int(forks)) + 1) \
        * rho_discovery_timeout

    log.info('Attempting connection discovery to %d systems'
             ' with auth "%s" using a timeout of %d minutes.',
             total_hosts_count, credential.get('name'), discovery_timeout)
    print(_('Attempting connection discovery to %d systems'
            ' with auth "%s" using a timeout of %d minutes.' %
            (total_hosts_count, credential.get('name'), discovery_timeout)))

    cmd_string = 'ansible alpha -m raw' \
                 ' -i ' + PING_INVENTORY_PATH \
                 + ' --ask-vault-pass -f ' + forks \
                 + ' --ssh-common-args="-o ServerAliveInterval=10"' \
                 + ' -a \'echo "Hello"\''

    my_env = os.environ.copy()
    my_env["ANSIBLE_HOST_KEY_CHECKING"] = "False"
    my_env["ANSIBLE_NOCOLOR"] = "True"
    log_env = {'RHO_CREDENTIAL_NAME': credential.get('name'),
               'RHO_HOST_PROCESSED': '0',
               'RHO_HOST_SUCCESSFUL': '0',
               'RHO_HOST_UNREACHABLE': '0',
               'RHO_HOST_FAILED': '0'}
    # Don't pass ansible_verbosity here as adding too much
    # verbosity can break our parsing of Ansible's output. This is
    # a temporary fix - a better solution would be less-fragile
    # output parsing.
    try:
        ansible_utils.run_with_vault(
            cmd_string, vault_pass,
            log_path=PING_LOG_PATH,
            env=my_env,
            log_to_stdout=process_discovery_scan,
            log_to_stdout_env=log_env,
            ansible_verbosity=0,
            timeout=discovery_timeout * 60,
            error_on_failure=False)
    except ansible_utils.AnsibleTimeoutException:
        # If the discovery scan times out, we'll just parse whatever
        # information we have in the log file.
        log.warning('Host discovery timed out. Gathering available host '
                    'information to proceed with scan.')

    with open(PING_LOG_PATH, 'r') as ping_log:
        success_hosts, failed_hosts, unreachable_hosts = \
            process_ping_output(ping_log)

    for host in success_hosts:
        success_auth_map[host].append(credential)
        success_port_map[host] = profile_port

    num_success = len(success_hosts)
    num_failed = len(failed_hosts)
    num_unreachable = len(unreachable_hosts)
    if num_success > 0:
        log.info('Connection succeeded with auth "%s" to %d systems.',
                 credential.get('name'), num_success)
        print(_('Connection succeeded with auth "%s" to %d systems.') %
              (credential.get('name'), num_success))
    if num_failed > 0:
        print(_('Failed to connect with auth "%s" to %d systems.') %
              (credential.get('name'), num_failed))
        log.info('Failed to connect with auth "%s" to %d systems.',
                 credential.get('name'), num_failed)
    if num_unreachable > 0:
        print(_('Found %d unreachable systems.') % (num_unreachable))
        log.info('Found %d unreachable systems.', num_unreachable)
    if num_success > 0 or num_failed > 0 or num_unreachable > 0:
        print('')

    return list(success_hosts), success_port_map, success_auth_map, \
        list(failed_hosts), list(unreachable_hosts)
