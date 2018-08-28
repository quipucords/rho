# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Scan for software on hosts in an inventory."""

from __future__ import print_function

import csv
import json
import os.path
import sys
import tempfile
import time

from rho import ansible_utils, postprocessing, utilities
from rho import vault as vault_module
from rho.translation import _ as t
from rho.utilities import str_to_ascii

DEFAULT_HOST_SCAN_TIMEOUT = 30


# Creates the filtered main inventory on which the custom
# modules to collect facts are run. This inventory can be
# used multiple times later after a profile has first been
# processed and the valid mapping as been figured out by
# pinging.
# pylint: disable=too-many-locals
def make_inventory_dict(hosts, port_map, auth_map, group_size=10):
    """Make the inventory for the scan, as a dict.

    :param hosts: a list of hosts for the inventory
    :param port_map: mapping from hosts to SSH ports
    :param auth_map: map from host IP to a list of auths it works with
    :param group_size: write hosts in groups of this size

    :returns: a dict with the structure:

        .. code-block:: python

            {'group1':
                 {'hosts':
                     {'IP address 1': {'host-vars-1'},
                      'IP address 2': {'host-vars-2'},
                      # ...
                     }
                 },
             'group2':
                 {'hosts':
                      ....
                 },
             ....
            }
    """

    # Create dict of successfully connected hosts
    host_dict = {}
    for host in hosts:
        ascii_host = str_to_ascii(host)
        ascii_port = str_to_ascii(str(port_map[host]))
        host_vars = {'ansible_host': ascii_host,
                     'ansible_port': ascii_port}
        host_vars.update(
            ansible_utils.auth_as_ansible_host_vars(auth_map[host][0]))
        host_dict[ascii_host] = host_vars

    result = {}
    keys = sorted(host_dict.keys())
    for group_num in range((len(keys) + group_size - 1) // group_size):
        start = group_num * group_size
        group_name = 'group' + str(group_num)
        result[group_name] = {'hosts': {}}
        for key in keys[start:start + group_size]:
            result[group_name]['hosts'][key] = host_dict[key]

    return result


def create_main_inventory(vault, hosts, port_map, auth_map, path):
    """Write an inventory file given the results of host discovery.

    :param vault: an Ansible vault to encrypt the results.
    :param hosts: a list of hosts in the inventory.
    :param port_map: a mapping from hosts to SSH port numbers.
    :param auth_map: a mapping from hosts to SSH credentials.
    :param path: the path to write the inventory.
    """

    yml_dict = make_inventory_dict(hosts, port_map, auth_map)
    vault.dump_as_yaml_to_file(yml_dict, path)
    ansible_utils.log_yaml_inventory('Main inventory', yml_dict)


# We can't just pass the group names from create_main_inventory to
# inventory_scan, because we might never call create_main_inventory if
# we use --cache. So we have to read the groups from the inventory
# file.
def hosts_by_group(yml_dict):
    """Get the hosts in each group from an inventory YAML file.

    Note: this works on inventory files written by
    create_main_inventory, but not on any Ansible inventory file.

    :param yml_dict: the Ansible inventory file, as a Python dict.

    :returns: a dict of the form
        {'group name': ['host1', 'host2', ...],
         ... }
    """
    hosts_by_group_dict = dict((group, list(yml_dict[group]['hosts'].keys()))
                               for i, group in enumerate(yml_dict.keys()))

    return hosts_by_group_dict


def process_host_vars(facts_to_collect, vars_by_host):
    """Process Ansible output into output facts.

    :param facts_to_collect: list of facts to collect.
    :param vars_by_host: dictionary (host: facts dictionary)
    :returns: list of per host fact dicitionaries
    """
    facts_out = []
    for _, host_vars in utilities.iteritems(vars_by_host):
        this_host = {}

        try:
            this_host.update(host_vars.get('connection', {}))
            this_host.update(host_vars.get('cpu', {}))
            this_host.update(host_vars.get('date', {}))
            this_host.update(host_vars.get('dmi', {}))
            this_host.update(host_vars.get('etc_release', {}))
            this_host.update(host_vars.get('file_contents', {}))
            this_host.update(host_vars.get('redhat_packages', {}))
            this_host.update(host_vars.get('redhat_release', {}))
            this_host.update(host_vars.get('subman', {}))
            this_host.update(host_vars.get('uname', {}))
            this_host.update(host_vars.get('virt', {}))
            this_host.update(host_vars.get('virt_what', {}))

            this_host.update(
                postprocessing.process_jboss_versions(facts_to_collect,
                                                      host_vars))
            this_host.update(
                postprocessing.process_addon_versions(facts_to_collect,
                                                      host_vars))
            this_host.update(
                postprocessing.process_id_u_jboss(facts_to_collect,
                                                  host_vars))
            this_host.update(
                postprocessing.process_jboss_eap_common_files(
                    facts_to_collect, host_vars))
            this_host.update(
                postprocessing.process_jboss_eap_processes(
                    facts_to_collect, host_vars))
            this_host.update(
                postprocessing.process_jboss_eap_packages(
                    facts_to_collect, host_vars))
            this_host.update(
                postprocessing.process_jboss_eap_locate(
                    facts_to_collect, host_vars))
            this_host.update(
                postprocessing.process_jboss_eap_init_files(
                    facts_to_collect, host_vars))
            this_host.update(
                postprocessing.process_jboss_eap_home(facts_to_collect,
                                                      host_vars))
            this_host.update(
                postprocessing.process_fuse_on_eap(facts_to_collect,
                                                   host_vars))
            this_host.update(
                postprocessing.process_karaf_home(facts_to_collect,
                                                  host_vars))
            this_host.update(
                postprocessing.process_fuse_init_files(
                    facts_to_collect, host_vars))
            this_host.update(
                postprocessing.process_brms_output(facts_to_collect,
                                                   host_vars))
            this_host.update(postprocessing.process_find_jboss_modules_jar(
                facts_to_collect, host_vars))
            this_host.update(postprocessing.process_find_karaf_jar(
                facts_to_collect, host_vars))

            postprocessing.handle_systemid(facts_to_collect, this_host)
            postprocessing.handle_redhat_packages(facts_to_collect, this_host)
            postprocessing.escape_characters(this_host)
            this_host.update(postprocessing.generate_eap_summary(
                facts_to_collect, this_host))
            this_host.update(postprocessing.generate_fuse_summary(
                facts_to_collect, this_host))

            # After all of the facts have been generated, remove -mr facts
            # which were for machine use only.
            keys = list(this_host.keys())
            for key in keys:
                if key[-3:] == '-mr':
                    del this_host[key]

            facts_out.append(this_host)
        except Exception as processing_error:  # pylint: disable=broad-except
            utilities.log.error('Error during processing.')
            utilities.log.exception(processing_error)

    return facts_out


def write_fact_report(facts_to_collect, facts_out, report_path):
    """Write fact report.

    :param facts_to_collect: The set of facts to output in the report
    :param facts_out: list of per host fact dicitionaries
    :param report_path: The path to output the report
    """
    normalized_path = os.path.normpath(report_path)
    with open(normalized_path, 'w') as write_file:
        # Construct the CSV writer
        writer = csv.DictWriter(
            write_file, sorted(facts_to_collect), delimiter=',',
            extrasaction='ignore')

        # Write a CSV header if necessary
        file_size = os.path.getsize(normalized_path)
        if file_size == 0:
            # handle Python 2.6 not having writeheader method
            if sys.version_info[0] == 2 and sys.version_info[1] <= 6:
                headers = {}
                for fields in writer.fieldnames:
                    headers[fields] = fields
                writer.writerow(headers)
            else:
                writer.writeheader()

        # Write the data
        for data in facts_out:
            writer.writerow(data)


# pylint: disable=too-many-arguments, too-many-statements, too-many-branches
def inventory_scan(hosts_yml_path, facts_to_collect, report_path,
                   vault_pass, base_name, forks=None,
                   scan_dirs=None, log_path=None, verbosity=0):
    """Run an inventory scan.

    :param hosts_yml_path: path to an Ansible inventory file to scan.
    :param facts_to_collect: a list of facts to collect.
    :param report_path: the path to write a report to.
    :param vault_pass: the vault password used to protect user data
    :param base_name: the base name of the output files
    :param forks: the number of Ansible forks, or None for default.
    :param scan_dirs: the directories on the remote host to scan, or None for
        default.
    :param log_path: path to log to, or None for default.
    :param verbosity: number of v's of Ansible verbosity.

    :returns: True if scan completed successfully, False if not.
    """
    hosts_yml = base_name + utilities.PROFILE_HOSTS_SUFIX
    hosts_yml_path = utilities.get_config_path(hosts_yml)

    vault = vault_module.Vault(vault_pass)
    hosts_dict = vault.load_as_yaml(hosts_yml_path)
    host_groups = hosts_by_group(hosts_dict)

    variables_prefix = os.path.join(
        tempfile.gettempdir(),
        'rho-fact-temp-' + str(time.time()) + '-')

    if os.path.isfile(utilities.PLAYBOOK_DEV_PATH):
        playbook = utilities.PLAYBOOK_DEV_PATH
    elif os.path.isfile(utilities.PLAYBOOK_RPM_PATH):
        playbook = utilities.PLAYBOOK_RPM_PATH
    else:
        print(t("rho scan playbook not found locally or in '%s'")
              % playbook)
        sys.exit(1)

    log_path = log_path or utilities.SCAN_LOG_PATH

    my_env = os.environ.copy()
    my_env["ANSIBLE_HOST_KEY_CHECKING"] = "False"
    my_env["ANSIBLE_NOCOLOR"] = "True"

    facts_out = []
    total_hosts_count = 0
    for group in host_groups.keys():
        hosts = host_groups.get(group, [])
        total_hosts_count += len(hosts)

    utilities.log.info('Starting scan of %d systems broken into %d groups.',
                       total_hosts_count, len(host_groups.keys()))
    print('\nStarting scan of %d systems broken into %d groups.' %
          (total_hosts_count, len(host_groups.keys())))
    for group in host_groups.keys():
        variables_path = variables_prefix + group
        hosts = host_groups.get(group, [])
        ansible_vars = {'facts_to_collect': list(facts_to_collect),
                        'scan_dirs': ' '.join(scan_dirs or []),
                        'variables_path': variables_path}

        cmd_string = ('ansible-playbook {playbook} '
                      '--limit {group},localhost '
                      '-i {inventory} -f {forks} '
                      '--ask-vault-pass '
                      '--extra-vars \'{vars}\'').format(
                          group=group,
                          playbook=playbook,
                          inventory=hosts_yml_path,
                          forks=forks,
                          vars=json.dumps(ansible_vars))

        rho_host_scan_timeout = os.getenv(
            'RHO_HOST_SCAN_TIMEOUT', DEFAULT_HOST_SCAN_TIMEOUT)

        try:
            rho_host_scan_timeout = int(rho_host_scan_timeout)
        except ValueError:
            rho_host_scan_timeout = DEFAULT_HOST_SCAN_TIMEOUT

        host_scan_timeout = ((len(hosts) // int(forks)) + 1) \
            * rho_host_scan_timeout
        utilities.log.info('Starting scan for group "%s" with %d systems'
                           ' with timeout of %d minutes.',
                           group, len(hosts), host_scan_timeout)
        print('\nStarting scan for group "%s" with %d systems'
              ' with timeout of %d minutes.\n' %
              (group, len(hosts), host_scan_timeout))
        try:
            ansible_utils.run_with_vault(
                cmd_string, vault_pass,
                env=my_env,
                log_path=log_path,
                log_to_stdout=utilities.process_host_scan,
                ansible_verbosity=verbosity,
                timeout=host_scan_timeout * 60,
                print_before_run=True)
        except ansible_utils.AnsibleProcessException as ex:
            print(t("An error has occurred during the scan. Please review" +
                    " the output to resolve the given issue: %s" % str(ex)))
            sys.exit(1)
        except ansible_utils.AnsibleTimeoutException as ex:
            utilities.log.warning('Scan for group "%s" timed out. Hosts \n'
                                  '%s\nwill be skipped. The rest of the scan '
                                  'is not affected.',
                                  group, host_groups[group])
            continue

        if os.path.isfile(variables_path):
            with open(variables_path, 'r') as variables_file:
                vars_by_host = {}
                update_json = json.load(variables_file)
                for host in hosts:
                    host_facts = update_json.get(host, {})
                    vars_by_host[host] = host_facts
                os.remove(variables_path)
                utilities.log.info('Processing scan data for %d more systems.',
                                   len(hosts))
                print('\nProcessing scan data for %d more systems.' %
                      (len(hosts)))
                group_facts = process_host_vars(facts_to_collect, vars_by_host)
                facts_out += group_facts
                utilities.log.info('Completed scanning %d systems.',
                                   len(facts_out))
                print('Completed scanning %d systems.\n' %
                      (len(facts_out)))

        else:
            utilities.log.error('Error collecting data for group %s.'
                                'output file %s not found.',
                                group, variables_path)

    if facts_out == []:
        print(t("An error has occurred during the scan. " +
                "No data was collected for any groups. " +
                "Please review the output to resolve the given issues"))
        sys.exit(1)

    write_fact_report(facts_to_collect, facts_out, report_path)
