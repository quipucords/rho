# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Postprocessing for facts coming from our Ansible playbook."""

# pylint: disable=too-many-lines

from __future__ import print_function
import os.path
import sys
import xml

from rho import utilities
from rho.utilities import log

# for parsing systemid
if sys.version_info > (3,):
    import xmlrpc.client as xmlrpclib  # pylint: disable=import-error
    long = int  # pylint: disable=invalid-name,redefined-builtin
else:
    import xmlrpclib  # pylint: disable=import-error

EAP_CLASSIFICATIONS = {
    'JBoss_4_0_0': 'JBossAS-4',
    'JBoss_4_0_1_SP1': 'JBossAS-4',
    'JBoss_4_0_2': 'JBossAS-4',
    'JBoss_4_0_3_SP1': 'JBossAS-4',
    'JBoss_4_0_4_GA': 'JBossAS-4',
    'Branch_4_0': 'JBossAS-4',
    'JBoss_4_2_0_GA': 'JBossAS-4',
    'JBoss_4_2_1_GA': 'JBossAS-4',
    'JBoss_4_2_2_GA': 'JBossAS-4',
    'JBoss_4_2_3_GA': 'JBossAS-4',
    'JBoss_5_0_0_GA': 'JBossAS-5',
    'JBoss_5_0_1_GA': 'JBossAS-5',
    'JBoss_5_1_0_GA': 'JBossAS-5',
    'JBoss_6.0.0.Final': 'JBossAS-6',
    'JBoss_6.1.0.Final': 'JBossAS-6',
    '1.0.1.GA': 'JBossAS-7',
    '1.0.2.GA': 'JBossAS-7',
    '1.1.1.GA': 'JBossAS-7',
    '1.2.0.CR1': 'JBossAS-7',
    '1.2.0.Final': 'WildFly-8',
    '1.2.2.Final': 'WildFly-8',
    '1.2.4.Final': 'WildFly-8',
    '1.3.0.Beta3': 'WildFly-8',
    '1.3.0.Final': 'WildFly-8',
    '1.3.3.Final': 'WildFly-8',
    '1.3.4.Final': 'WildFly-9',
    '1.4.2.Final': 'WildFly-9',
    '1.4.3.Final': 'WildFly-9',
    '1.4.4.Final': 'WildFly-10',
    '1.5.0.Final': 'WildFly-10',
    '1.5.1.Final': 'WildFly-10',
    '1.5.2.Final': 'WildFly-10',
    'JBPAPP_4_2_0_GA': 'EAP-4.2',
    'JBPAPP_4_2_0_GA_C': 'EAP-4.2',
    'JBPAPP_4_3_0_GA': 'EAP-4.3',
    'JBPAPP_4_3_0_GA_C': 'EAP-4.3',
    'JBPAPP_5_0_0_GA': 'EAP-5.0.0',
    'JBPAPP_5_0_1': 'EAP-5.0.1',
    'JBPAPP_5_1_0': 'EAP-5.1.0',
    'JBPAPP_5_1_1': 'EAP-5.1.1',
    'JBPAPP_5_1_2': 'EAP-5.1.2',
    'JBPAPP_5_2_0': 'EAP-5.2.0',
    '1.1.2.GA-redhat-1': 'EAP-6.0.0',
    '1.1.3.GA-redhat-1': 'EAP-6.0.1',
    '1.2.0.Final-redhat-1': 'EAP-6.1.0',
    '1.2.2.Final-redhat-1': 'EAP-6.1.1',
    '1.3.0.Final-redhat-2': 'EAP-6.2',
    '1.3.3.Final-redhat-1': 'EAP-6.3',
    '1.3.4.Final-redhat-1': 'EAP-6.3',
    '1.3.5.Final-redhat-1': 'EAP-6.3',
    '1.3.6.Final-redhat-1': 'EAP-6.4',
    '1.3.7.Final-redhat-1': 'EAP-6.4',
    '1.4.4.Final-redhat-1': 'EAP-7.0',
    '1.5.1.Final-redhat-1': 'EAP-7.0',
    '1.5.4.Final-redhat-1': 'EAP-7.0'
}

BRMS_CLASSIFICATIONS = {
    '6.4.0.Final-redhat-3': 'BRMS 6.3.0',
    '6.3.0.Final-redhat-5': 'BRMS 6.2.0',
    '6.2.0.Final-redhat-4': 'BRMS 6.1.0',
    '6.0.3-redhat-6': 'BRMS 6.0.3',
    '6.0.3-redhat-4': 'BRMS 6.0.2',
    '6.0.2-redhat-6': 'BRMS 6.0.1',
    '6.0.2-redhat-2': 'BRMS 6.0.0',
    '5.3.1.BRMS': 'BRMS 5.3.1',
    '5.3.0.BRMS': 'BRMS 5.3.0',
    '5.2.0.BRMS': 'BRMS 5.2.0',
    '5.1.0.BRMS': 'BRMS 5.1.0',
    '5.0.2.BRMS': 'BRMS 5.0.2',
    '5.0.1.BRMS': 'BRMS 5.0.1',
    'drools-core-5.0.0': 'BRMS 5.0.0',
    '6.5.0.Final': 'Drools 6.5.0'
}

FUSE_CLASSIFICATIONS = {
    'redhat-630187': 'Fuse-6.3.0',
    'redhat-621084': 'Fuse-6.2.1',
    'redhat-620133': 'Fuse-6.2.0',
    'redhat-611412': 'Fuse-6.1.1',
    'redhat-610379': 'Fuse-6.1.0',
    'redhat-60024': 'Fuse-6.0.0',
}


def raw_output_present(fact_names, host_vars, this_fact, this_var, command):
    """Basic sanity checks for processing an Ansible raw command.

    :param fact_names: the facts to be collected
    :param host_vars: all variables collected for a host
    :param this_fact: the name of the fact we are processing
    :param this_var: the name that Ansible has for our output
    :param command: the command that was run

    :returns: a tuple of
        (None or error dict, None or raw command output).
        The error dict is suitable for inclusion in the rho output
        dictionary. There will not be both errors and raw command
        output. If raw command output is returned, it will have
        fields 'rc' and 'stdout_lines' or 'results'.

    Usage:
        err, output = raw_output_present(...)
        if err is not None:
            return err

        ... process output ...
    """

    if this_var not in host_vars:
        if this_fact not in fact_names:
            return {}, None

        return {this_fact: 'Error: "{0}" not run'.format(command)}, None

    raw_output = host_vars[this_var]

    if (('rc' not in raw_output or
         'stdout_lines' not in raw_output) and 'results' not in raw_output):
        return (
            {this_fact:
             'Error: could not get output from "{0}"'.format(command)},
            None)

    return None, raw_output


# MR is "machine readable". User-friendly string-based fact FOO has a
# machine-friendly representation at fact_dict[FOO + MR]. (Only some
# facts have MR representations so far.)
MR = '-mr'

JBOSS_EAP_INSTALLED_VERSIONS = 'jboss.eap.installed-versions'
JBOSS_EAP_DEPLOY_DATES = 'jboss.eap.deploy-dates'
JBOSS_EAP_RUNNING_PATHS = 'jboss.eap.running-paths'

FIND_WARNING = 'find: WARNING: Hard link count is wrong for /proc: this may' \
    ' be a bug in your filesystem driver.'
GENERIC_ERROR = 'error'


# JBoss versions are processed separately from other *-ver data
# because they merge data from two input facts and include deploy
# dates as well as version strings.
# pylint: disable=too-many-branches
def process_jboss_versions(fact_names, host_vars):
    """Get JBoss version information from the host_vars.

    :param fact_names: the set of fact names the user requested.
    :param host_vars: the host vars from Ansible.
    :returns: a dict of key-value pairs to output.
    """

    lines = []
    val = {}

    # host_vars is not used after this function (data that we return
    # is copied to host_vals instead), so by not adding
    # jboss.eap.jar_ver and jboss.eap.run_jar_ver to val, we are
    # implicitly removing them from the output.
    err, output = raw_output_present(fact_names, host_vars,
                                     'jboss.eap.jar-ver',
                                     'jboss.eap.jar-ver',
                                     'scan for jboss-modules.jar')
    if err is not None:
        return err
    lines.extend(output['stdout_lines'])

    err, output = raw_output_present(fact_names, host_vars,
                                     'jboss.eap.run-jar-ver',
                                     'jboss.eap.run-jar-ver',
                                     'scan for running JBoss EAP')
    if err is not None:
        return err
    lines.extend(output['stdout_lines'])

    jboss_releases = []
    deploy_dates = []
    for line in lines:
        if line:
            line_format = line.split('**')
            version = line_format[0]
            deploy_date = line_format[-1]
            deploy_dates.append(deploy_date)
            if version in EAP_CLASSIFICATIONS:
                jboss_releases.append(EAP_CLASSIFICATIONS[version])
            elif version.strip():
                jboss_releases.append('Unknown-Release: ' + version)

    def empty_output_message(val, name):
        """Give the right error message for missing data.

        For data that depends on having Java.

        :param val: a value. Considered missing if falsey.
        :param name: the thing we were searching for.
        :returns: the val if true, otherwise a useful error message.
        """

        if val:
            return val
        if not host_vars['have_java']:
            return 'N/A (java not found)'
        return '({0} not found)'.format(name)

    if JBOSS_EAP_INSTALLED_VERSIONS in fact_names:
        val[JBOSS_EAP_INSTALLED_VERSIONS] = (
            empty_output_message('; '.join(jboss_releases), 'jboss'))
        val[JBOSS_EAP_INSTALLED_VERSIONS + MR] = jboss_releases
    if JBOSS_EAP_DEPLOY_DATES in fact_names:
        val[JBOSS_EAP_DEPLOY_DATES] = (
            empty_output_message('; '.join(deploy_dates), 'jboss'))
        val[JBOSS_EAP_DEPLOY_DATES + MR] = deploy_dates
    if JBOSS_EAP_RUNNING_PATHS in fact_names:
        err, output = raw_output_present(fact_names, host_vars,
                                         JBOSS_EAP_RUNNING_PATHS,
                                         'jboss_eap_running_paths',
                                         'running EAP scan')
        if err is not None:
            val.update(err)
        elif FIND_WARNING in output['stdout']:
            val[JBOSS_EAP_RUNNING_PATHS] = GENERIC_ERROR
        else:
            val[JBOSS_EAP_RUNNING_PATHS] = empty_output_message(
                output['stdout'], 'running EAP scan')
            if host_vars['have_java']:
                val[JBOSS_EAP_RUNNING_PATHS + MR] = output['stdout']

    return val


def classify_releases(lines, classifications):
    """Classify release strings using a dictionary."""

    releases = []
    for line in lines:
        if line:
            if line in classifications:
                releases.append(classifications[line])
            else:
                releases.append('Unknown-Release: ' + line)

    return '; '.join(releases)


def process_addon_versions(fact_names, host_vars):
    """Classify release strings for JBoss BRMS and FUSE.

    :param fact_names: the set of fact names that the user requested.
    :param host_vars: the host vars from Ansible.
    :returns: a dict of key-value pairs to output.
    """

    result = {}

    def classify(key, fact_names, classifications):
        """Classify a particular key."""

        if key in fact_names:
            err, output = raw_output_present(fact_names, host_vars,
                                             key, key, key)
            if err is not None:
                result.update(err)
                return

            classes = classify_releases(output['stdout_lines'],
                                        classifications)
            if classes:
                result[key] = classes
            else:
                result[key] = '({0} not found)'.format(key)

    classify('jboss.brms.kie-api-ver', fact_names, BRMS_CLASSIFICATIONS)
    classify('jboss.brms.drools-core-ver', fact_names, BRMS_CLASSIFICATIONS)
    classify('jboss.brms.kie-war-ver', fact_names, BRMS_CLASSIFICATIONS)

    classify('jboss.activemq-ver', fact_names, FUSE_CLASSIFICATIONS)
    classify('jboss.camel-ver', fact_names, FUSE_CLASSIFICATIONS)
    classify('jboss.cxf-ver', fact_names, FUSE_CLASSIFICATIONS)

    return result


JBOSS_EAP_JBOSS_USER = 'jboss.eap.jboss-user'


def process_id_u_jboss(fact_names, host_vars):
    """Process the output from 'id -u jboss', as run by Ansible

    :returns: a dict of key-value pairs to add to the output.
    """

    # We use the 'id' command to check for jboss because it's been in
    # GNU coreutils since 1992, so it should be present on every
    # system we encounter.

    err, output = raw_output_present(fact_names, host_vars,
                                     'jboss.eap.jboss-user',
                                     'jboss_eap_id_jboss',
                                     'id -u jboss')
    if err is not None:
        return err

    if output['rc'] == 0:
        return {JBOSS_EAP_JBOSS_USER: "User 'jboss' present",
                JBOSS_EAP_JBOSS_USER + MR: True}

    # Don't output a definitive "not found" unless we see an error
    # string that we recognize. We don't want to assume that any
    # nonzero error code means "not found", because then we would give
    # false negatives if the user didn't have permission to read
    # /etc/passwd (or other errors).
    if (output['stdout_lines'] == ['id: jboss: no such user'] or
            output['stdout_lines'] == ['id: jboss: No such user']):
        return {JBOSS_EAP_JBOSS_USER: 'No user "jboss" found',
                JBOSS_EAP_JBOSS_USER + MR: False}

    return {JBOSS_EAP_JBOSS_USER:
            'Error: unexpected output from "id -u jboss": %s' % output}


JBOSS_EAP_COMMON_FILES = 'jboss.eap.common-files'


def process_jboss_eap_common_files(fact_names, host_vars):
    """Process the output of 'test -e <dir>', for common install paths.

    :returns: a dict of key, value pairs to add to the output.
    """

    err, output = raw_output_present(fact_names, host_vars,
                                     'jboss.eap.common-files',
                                     'jboss_eap_common_files',
                                     'common file and directory tests')

    if err is not None:
        return err

    items = output['results']

    out_list = []
    for item in items:
        directory = item['item']

        if 'rc' in item and item['rc'] == 0:
            out_list.append(directory)

        # If 'rc' is in item but is nonzero, the directory wasn't
        # present. If 'rc' isn't in item, there was an error and the
        # test wasn't run. Unfortunately, we don't have the ability to
        # get logs out of spit_results, so we'll have to hope the
        # scan_log is enough to debug any problems we have. :(

    return {JBOSS_EAP_COMMON_FILES:
            ';'.join(('{0} found'.format(directory)
                      for directory in out_list)),
            JBOSS_EAP_COMMON_FILES + MR: out_list}


JBOSS_EAP_PROCESSES = 'jboss.eap.processes'


def process_jboss_eap_processes(fact_names, host_vars):
    """Process the output of 'ps -A -f e | grep eap'

    :returns: a dict of key, value pairs to add to the output.
    """

    # Why use 'ps -A -f e | grep eap'? The -A gets us every process on
    # the system, and -f means ps will print the command-line
    # arguments, which is key because JBoss will be invoked with java
    # as the executable and an argument that says to run the Wildfly
    # jar.

    # The e makes ps print the process's environment. It's in a format
    # that is not machine-readable, because ps uses spaces as the
    # delimiter for both command-line args and the process
    # environment, and we have no way to tell where the arguments end
    # and the environment begins. However, that's fine for grepping. I
    # observed an EAP 7 application server running with MANPATH,
    # JBOSS_MODULEPATH, JBOSS_HOME, WILDFLY_CONSOLE_LOG, WILDFLY_SH,
    # LD_LIBRARY_PATH, EAP7_SCLS_ENABLED, PATH, WILDFLY_MODULEPATH,
    # HOME, and PKG_CONFIG_PATH set to directories that included
    # /opt/rh/eap7, all of which will be caught by our
    # grep. Additionally, variables LAUNCH_JBOSS_IN_BACKGROUND and
    # JBOSS_HOME will be caught because of the variable names
    # themselves. We deliberately don't grep for wildfly or jboss,
    # because that could catch non-JBoss Wildfly installations.

    err, output = raw_output_present(fact_names, host_vars,
                                     JBOSS_EAP_PROCESSES,
                                     JBOSS_EAP_PROCESSES,
                                     'ps -A -f e | grep eap')
    if err is not None:
        return err

    # pgrep exists with status 0 if it finds processes matching its
    # pattern, and status 1 if not.
    if output['rc']:
        return {JBOSS_EAP_PROCESSES: 'No EAP processes found',
                JBOSS_EAP_PROCESSES + MR: 0}

    num_procs = len(output['stdout_lines'])

    # There should always be two processes matching 'eap', one for the
    # grep that's searching for 'eap', and one for the bash that's
    # running the pipeline.
    if num_procs < 2:
        return {
            JBOSS_EAP_PROCESSES:
            "Bad result ({0} processes) from 'ps -A -f e | grep eap'".format(
                num_procs)}

    return {JBOSS_EAP_PROCESSES:
            '{0} EAP processes found'.format(num_procs - 2),
            JBOSS_EAP_PROCESSES + MR: num_procs - 2}


JBOSS_EAP_PACKAGES = 'jboss.eap.packages'


def process_jboss_eap_packages(fact_names, host_vars):
    """Process the list of JBoss EAP-related RPMs.

    :returns: a dict of key, value pairs to add to the output.
    """

    # We use (eap7)|(jbossas) as the pattern because all of the EAP 6
    # packages had the prefix jbossas- and all of the EAP 7 packages
    # have the prefix eap7-. We set a custom format for rpm output and
    # get a lot of package fields, even though we only use the number
    # of output lines, so we will have full package data in the logs
    # if customers have questions about the number. Hopefully in the
    # future we can surface that data through a UI.

    err, output = raw_output_present(fact_names, host_vars,
                                     JBOSS_EAP_PACKAGES,
                                     JBOSS_EAP_PACKAGES,
                                     "rpm -q -a | grep -E '(eap7)|(jbossas)'")
    if err is not None:
        return err

    # the sort on the end of the pipeline returns 0 whether or not
    # matches were found, so a nonzero return code should never
    # happen.
    if output['rc']:
        return {JBOSS_EAP_PACKAGES: 'Pipeline returned non-zero status'}

    num_packages = len(output['stdout_lines'])

    return {JBOSS_EAP_PACKAGES:
            '{0} JBoss-related packages found'.format(num_packages),
            JBOSS_EAP_PACKAGES + MR: num_packages}


JBOSS_EAP_LOCATE_JBOSS_MODULES_JAR = 'jboss.eap.locate-jboss-modules-jar'


def process_jboss_eap_locate(fact_names, host_vars):
    """Process the results of 'locate jboss-modules.jar'.

    :returns: a dict of key, value pairs to add to the output.
    """

    if not host_vars['have_locate']:
        return {JBOSS_EAP_LOCATE_JBOSS_MODULES_JAR:
                'N/A (locate not found)'}

    err, output = raw_output_present(fact_names, host_vars,
                                     JBOSS_EAP_LOCATE_JBOSS_MODULES_JAR,
                                     'jboss_eap_locate_jboss_modules_jar',
                                     'locate jboss-modules.jar')
    if err is not None:
        return err

    if not output['rc'] and output['stdout_lines']:
        return {JBOSS_EAP_LOCATE_JBOSS_MODULES_JAR:
                ';'.join(output['stdout_lines']),
                JBOSS_EAP_LOCATE_JBOSS_MODULES_JAR + MR:
                output['stdout_lines']}

    if output['rc'] and not output['stdout_lines']:
        return {JBOSS_EAP_LOCATE_JBOSS_MODULES_JAR:
                'jboss-modules.jar not found'}

    return {JBOSS_EAP_LOCATE_JBOSS_MODULES_JAR:
            "Error code {0} running 'locate jboss-modules.jar': {1}".format(
                output['rc'], output['stdout'])}


JBOSS_EAP_INIT_FILES = 'jboss.eap.init-files'


def process_jboss_eap_init_files(fact_names, host_vars):
    """Look for jboss and EAP in init system output.

    :returns: a dict of key, value pairs to add to the output.
    """

    # The init system changed between RHEL 6 and RHEL 7. 'chkconfig'
    # should work on RHEL 6, and 'systemctl list-unit-files' should
    # work on RHEL 7.
    err, chkconfig = raw_output_present(fact_names, host_vars,
                                        JBOSS_EAP_INIT_FILES,
                                        'jboss_eap_chkconfig',
                                        'chkconfig')
    if err is not None:
        return err

    err, systemctl = raw_output_present(fact_names, host_vars,
                                        JBOSS_EAP_INIT_FILES,
                                        'jboss_eap_systemctl_unit_files',
                                        'systemctl list-unit-files')
    if err is not None:
        return err

    if chkconfig['rc'] and systemctl['rc']:
        return {JBOSS_EAP_INIT_FILES:
                'Error: all init system checks failed.'}

    # On a RHEL 6 system, chkconfig will return a list of available
    # services and systemctl will error. On a RHEL 7 system, systemctl
    # will return a list of system services and chkconfig will return
    # a shorter list of services and a warning message to go look at
    # systemctl. However, users may well choose to run JBoss under the
    # old init system on RHEL 7 due to familiarity or lack of need to
    # change, so we look in all available output.

    def find_services(lines, method):
        """Find system services matching 'jboss' or 'eap'

        :returns: a list of the services, as strings, with the method.
        """

        output = []
        for line in lines:
            if not line:
                continue

            service = line.split()[0]
            if 'jboss' in service or 'eap' in service:
                output.append('{0} ({1})'.format(service, method))

        return output

    found_services = []
    if not chkconfig['rc']:
        found_services.extend(find_services(chkconfig['stdout_lines'],
                                            'chkconfig'))
    if not systemctl['rc']:
        found_services.extend(find_services(systemctl['stdout_lines'],
                                            'systemctl'))

    if found_services:
        return {JBOSS_EAP_INIT_FILES:
                '; '.join(found_services),
                JBOSS_EAP_INIT_FILES + MR:
                found_services}

    return {JBOSS_EAP_INIT_FILES:
            "No services found matching 'jboss' or 'eap'."}


JBOSS_EAP_EAP_HOME = 'jboss.eap.eap-home'
# Files that live in an EAP_HOME directory.
JBOSS_EAP_INDICATOR_FILES = ['appclient', 'standalone', 'JBossEULA.txt',
                             'modules', 'jboss-modules.jar', 'version.txt']


def process_indicator_files(indicator_files, ls_out):
    """Process the output of a with_items ls from Ansible."""

    ls_results = {}
    ls_results_mr = {}
    for item in ls_out['results']:
        directory = item['item']
        if item['rc']:
            ls_results[directory] = "Error in 'ls'"
            ls_results_mr[directory] = []
            continue

        files = item['stdout_lines']
        found_in_dir = [filename for filename in indicator_files
                        if filename in files]
        if found_in_dir:
            ls_results[directory] = (
                directory + ' contains ' + ','.join(found_in_dir))
            ls_results_mr[directory] = found_in_dir
        else:
            ls_results[directory] = 'No indicator files found'
            ls_results_mr[directory] = []

    return ls_results, ls_results_mr


def process_cat_results(filename, cat_out):
    """Process the output of a with_items cat from Ansible."""

    cat_results = {}
    cat_results_mr = {}
    for item in cat_out['results']:
        directory = item['item']
        if item['rc']:
            cat_results[directory] = "Error in 'cat {0}'".format(filename)
            cat_results_mr[directory] = False
        else:
            file_contents = item['stdout'].strip()
            cat_results[directory] = file_contents
            cat_results_mr[directory] = 'Red Hat' in file_contents

    return cat_results, cat_results_mr


def process_jboss_eap_home(fact_names, host_vars):
    """Find the EAP_HOME directory of a JBoss installation, if possible."""

    err, ls_out = raw_output_present(fact_names, host_vars,
                                     JBOSS_EAP_EAP_HOME,
                                     'eap_home_candidates_ls',
                                     'ls -1 EAP_HOME candidate directories')
    if err is not None:
        return err

    err, cat_out = raw_output_present(fact_names, host_vars,
                                      JBOSS_EAP_EAP_HOME,
                                      'eap_home_candidates_version_txt',
                                      'cat EAP_HOME/version.txt for candidate '
                                      'EAP_HOMEs')
    if err is not None:
        return err

    ls_results, ls_results_mr = process_indicator_files(
        JBOSS_EAP_INDICATOR_FILES, ls_out)
    cat_results, cat_results_mr = process_cat_results('version.txt', cat_out)

    eap_homes = ls_results.keys()
    assert eap_homes == cat_results.keys()

    # The MR results are a list of all of the directories that are
    # likely EAP_HOME directories.
    results_mr = [directory
                  for directory in eap_homes
                  if ls_results_mr.get(directory) or
                  cat_results_mr.get(directory)]

    return {JBOSS_EAP_EAP_HOME:
            '; '.join([directory +
                       ': ' + ls_results.get(directory, '') +
                       ', ' + cat_results.get(directory, '')
                       for directory in eap_homes]),
            JBOSS_EAP_EAP_HOME + MR: results_mr}


JBOSS_EAP_SUMMARY = 'jboss.eap.summary'


def generate_eap_summary(facts_to_collect, facts):
    """Generate a single summary fact about whether the machine has EAP."""
    if JBOSS_EAP_SUMMARY not in facts_to_collect:
        return {}

    if JBOSS_EAP_SUMMARY not in facts_to_collect:
        return {}

    installed_versions = facts.get(JBOSS_EAP_INSTALLED_VERSIONS + MR)
    deploy_dates = facts.get(JBOSS_EAP_DEPLOY_DATES + MR)
    running_paths = facts.get(JBOSS_EAP_RUNNING_PATHS + MR)
    jboss_user = facts.get(JBOSS_EAP_JBOSS_USER + MR)
    common_files = facts.get(JBOSS_EAP_COMMON_FILES + MR)
    eap_processes = facts.get(JBOSS_EAP_PROCESSES + MR)
    packages = facts.get(JBOSS_EAP_PACKAGES + MR)
    modules_jar = facts.get(JBOSS_EAP_LOCATE_JBOSS_MODULES_JAR + MR)
    init_files = facts.get(JBOSS_EAP_INIT_FILES + MR)
    eap_home = facts.get(JBOSS_EAP_EAP_HOME + MR)

    # pylint: disable=too-many-boolean-expressions
    if (installed_versions or
            deploy_dates or
            running_paths or
            packages or
            modules_jar or
            eap_home):  # noqa (indent)
        return {JBOSS_EAP_SUMMARY: 'Yes, EAP installation present'}

    if (jboss_user or
            common_files or
            eap_processes or
            init_files):  # noqa (indent)
        return {JBOSS_EAP_SUMMARY:
                'Maybe - an EAP installation may be present'}

    return {JBOSS_EAP_SUMMARY: 'No EAP installation detected'}


JBOSS_EAP_FIND_JBOSS_MODULES_JAR = 'jboss.eap.find-jboss-modules-jar'


def process_find_jboss_modules_jar(fact_names, host_vars):
    """Process the output of 'find jboss-modules.jar'"""

    if JBOSS_EAP_FIND_JBOSS_MODULES_JAR not in fact_names:
        return {}

    err, out = raw_output_present(fact_names, host_vars,
                                  JBOSS_EAP_FIND_JBOSS_MODULES_JAR,
                                  'jboss_eap_find_jboss_modules_jar',
                                  'find jboss-modules.jar')
    if err is not None:
        return err

    return {JBOSS_EAP_FIND_JBOSS_MODULES_JAR: '; '.join(out['stdout_lines'])}


FIND_KARAF_JAR = 'jboss.fuse-on-karaf.find-karaf-jar'


def process_find_karaf_jar(fact_names, host_vars):
    """Process the output of 'find karaf.jar'"""

    if FIND_KARAF_JAR not in fact_names:
        return {}

    err, out = raw_output_present(fact_names, host_vars,
                                  FIND_KARAF_JAR,
                                  'karaf_find_karaf_jar',
                                  'find karaf.jar')
    if err is not None:
        return err

    return {FIND_KARAF_JAR: '; '.join(out['stdout_lines'])}


JBOSS_FUSE_FUSE_ON_EAP = 'jboss.fuse.fuse-on-eap'
JBOSS_FUSE_BIN_INDICATOR_FILES = ['fuseconfig.sh', 'fusepatch.sh']


def process_fuse_on_eap(fact_names, host_vars):
    """Find JBoss Fuse when it is layered on top of JBoss EAP."""

    if JBOSS_FUSE_FUSE_ON_EAP not in fact_names:
        return {}

    err, ls_bin = raw_output_present(fact_names, host_vars,
                                     JBOSS_FUSE_FUSE_ON_EAP,
                                     'eap_home_candidates_bin',
                                     'ls $EAP_HOME/bin')
    if err:
        return err

    err, layers_conf = raw_output_present(fact_names, host_vars,
                                          JBOSS_FUSE_FUSE_ON_EAP,
                                          'eap_home_candidates_layers_conf',
                                          'cat $EAP_HOME/modules/layers.conf')
    if err:
        return err

    err, ls_layers = raw_output_present(fact_names, host_vars,
                                        JBOSS_FUSE_FUSE_ON_EAP,
                                        'eap_home_candidates_layers',
                                        'ls $EAP_HOME/modules/system/layers')
    if err:
        return err

    ls_bin_results, ls_bin_mr = process_indicator_files(
        JBOSS_FUSE_BIN_INDICATOR_FILES, ls_bin)
    layers_conf_results, layers_conf_mr = process_cat_results('layers.conf',
                                                              layers_conf)
    ls_layers_results, ls_layers_mr = process_indicator_files(['fuse'],
                                                              ls_layers)

    eap_homes = ls_bin_results.keys()
    assert eap_homes == layers_conf_results.keys() == ls_layers_results.keys()

    return {JBOSS_FUSE_FUSE_ON_EAP:
            '; '.join([
                ('{0}: /bin={1}, /modules/layers.conf={2},'
                 ' /modules/system/layers={3}').format(
                     eap_home,
                     ls_bin_results[eap_home],
                     layers_conf_results[eap_home],
                     ls_layers_results[eap_home])
                for eap_home in eap_homes]),
            JBOSS_FUSE_FUSE_ON_EAP + MR:
            {eap_home:
             (ls_bin_mr[eap_home] or
              layers_conf_mr[eap_home] or
              ls_layers_mr[eap_home])
             for eap_home in eap_homes}}


JBOSS_FUSE_ON_KARAF_KARAF_HOME = 'jboss.fuse-on-karaf.karaf-home'


def process_karaf_home(fact_names, host_vars):
    """Process karaf_home indicators to detect Fuse-on-Karaf."""

    if (JBOSS_FUSE_ON_KARAF_KARAF_HOME not in fact_names and
            JBOSS_FUSE_SUMMARY not in fact_names):  # noqa
        return {}

    if 'karaf_homes' not in host_vars:
        return {JBOSS_FUSE_ON_KARAF_KARAF_HOME:
                'Error: fact karaf_homes not collected.'}
    karaf_homes = host_vars['karaf_homes']

    err, bin_fuse = raw_output_present(fact_names, host_vars,
                                       JBOSS_FUSE_ON_KARAF_KARAF_HOME,
                                       'karaf_home_bin_fuse',
                                       'ls -1 KARAF_HOME/bin/fuse')
    if err is not None:
        return err

    err, system_org_jboss = raw_output_present(
        fact_names, host_vars,
        JBOSS_FUSE_ON_KARAF_KARAF_HOME,
        'karaf_home_system_org_jboss',
        'ls -1 KARAF_HOME/system/org/jboss')
    if err is not None:
        return err

    system_org_jboss_results, system_org_jboss_mr = process_indicator_files(
        ['fuse'], system_org_jboss)

    bin_fuse_mr = {
        result['item']: result['rc'] == 0
        for result in bin_fuse['results']}

    bin_fuse_results = {
        directory: '/bin/fuse exists' if result else '/bin/fuse not found'
        for directory, result in utilities.iteritems(bin_fuse_mr)}

    assert list(system_org_jboss_results.keys()) == karaf_homes
    assert list(bin_fuse_results.keys()) == karaf_homes

    return {JBOSS_FUSE_ON_KARAF_KARAF_HOME:
            '; '.join(['{0}: {1}; {2}'.format(
                karaf_home,
                bin_fuse_results[karaf_home],
                system_org_jboss_results[karaf_home])
                       for karaf_home in karaf_homes]),
            JBOSS_FUSE_ON_KARAF_KARAF_HOME + MR:
            {karaf_home:
             system_org_jboss_mr[karaf_home] or bin_fuse_mr[karaf_home]
             for karaf_home in karaf_homes}}  # noqa


JBOSS_FUSE_INIT_FILES = 'jboss.fuse.init-files'


def process_fuse_init_files(fact_names, host_vars):
    """Process facts for jboss.fuse.init-files

    Note: these facts are included because they can be useful, but the
    filters are very susceptible to letting through lines which a
    human could easily tell are false positives, but we don't handle
    that automatically.
    """

    err, systemctl_out = raw_output_present(
        fact_names, host_vars,
        JBOSS_FUSE_INIT_FILES,
        'jboss_fuse_systemctl_unit_files',
        'systemctl list-unit-files | grep fuse')
    if err is not None:
        return err

    err, chkconfig_out = raw_output_present(fact_names, host_vars,
                                            JBOSS_FUSE_INIT_FILES,
                                            'jboss_fuse_chkconfig',
                                            'chkconfig | grep fuse')
    if err is not None:
        return err

    return {JBOSS_FUSE_INIT_FILES:
            'systemctl: {0}; chkconfig: {1}'.format(
                '; '.join(systemctl_out['stdout_lines']),
                '; '.join(chkconfig_out['stdout_lines']))}


def classify_kie_file(pathname):
    """Classify a kie-api-* file.

    :param pathname: the path to the file
    :returns: a BRMS version string, or None if not a Red Hat kie file.
    """

    # os.path.basename behaves differently if the last part of the
    # path ends in a /, so normalize.
    if pathname.endswith('/'):
        pathname = pathname[:-1]

    basename = os.path.basename(pathname)

    version_string = utilities.strip_suffix(
        utilities.strip_prefix(basename, 'kie-api-'),
        '.jar')

    if version_string in BRMS_CLASSIFICATIONS:
        return BRMS_CLASSIFICATIONS[version_string]

    if 'redhat' in version_string:
        return version_string

    return None


JBOSS_BRMS = 'jboss.brms'
UNKNOWN_BASE = 'unknown base directory'
JBOSS_BRMS_SUMMARY = 'jboss.brms.summary'


# pylint: disable=too-many-locals, too-many-branches
def process_brms_output(fact_names, host_vars):
    """Process facts for jboss.brms."""

    business_central_candidates = host_vars.get(
        'business_central_candidates', [])
    kie_server_candidates = host_vars.get(
        'kie_server_candidates', [])

    err, manifest_mf_out = raw_output_present(
        fact_names, host_vars,
        JBOSS_BRMS,
        'jboss_brms_manifest_mf',
        'cat {{ base_directory }}/META-INF/MANIFEST.MF')
    if err is not None:
        return err

    err, kie_in_business_central_out = raw_output_present(
        fact_names, host_vars,
        JBOSS_BRMS,
        'jboss_brms_kie_in_business_central',
        'ls -1 {{ base_directory }}/WEB-INF/lib/kie-api*')
    if err is not None:
        return err

    err, locate_kie_api_out = raw_output_present(
        fact_names, host_vars,
        JBOSS_BRMS,
        'jboss_brms_locate_kie_api',
        "locate --basename 'kie-api*'")
    if err is not None:
        return err

    base_directories = set(business_central_candidates + kie_server_candidates)

    # manifest_mfs maps directory name to MANIFEST.MF contents
    manifest_mfs = {}
    for result in manifest_mf_out['results']:
        manifest_mfs[result['item']] = result['stdout']
    if sorted(list(manifest_mfs.keys())) != sorted(list(base_directories)):
        log.error('Bad manifest keys: %s, %s',
                  manifest_mfs.keys(), base_directories)

    # Dud entry here matches the UNKNOWN_BASE member of
    # kie_versions_by_directory, which is where we keep kie-api files
    # that aren't in a base directory we recognize.
    manifest_mfs[UNKNOWN_BASE] = ''

    kie_files = set(locate_kie_api_out['stdout_lines'])

    for result in kie_in_business_central_out['results']:
        if result['rc']:
            continue

        for filename in result['stdout_lines']:
            kie_files.add(filename)

    find_kie_api_out = host_vars.get('jboss.brms.kie-api-ver')
    if find_kie_api_out and 'stdout_lines' in find_kie_api_out:
        for filename in find_kie_api_out['stdout_lines']:
            kie_files.add(filename)

    # These loops could be implemented as a single pass through both
    # lists if we pre-sorted them. Waiting to see if anyone cares
    # about the performance of this code before optimizing.
    kie_versions_by_directory = {}
    for directory in base_directories:
        versions_in_dir = set()
        for filename in list(kie_files):
            if filename.startswith(directory):
                kie_files.remove(filename)
                category = classify_kie_file(filename)
                if category:
                    versions_in_dir.add(category)
                # Deliberately drop files if their category is falsey,
                # because it means that they are not Red Hat files.
        kie_versions_by_directory[directory] = versions_in_dir
    versions_in_dir = set()
    for filename in list(kie_files):
        category = classify_kie_file(filename)
        if category:
            versions_in_dir.add(category)
    kie_versions_by_directory[UNKNOWN_BASE] = versions_in_dir

    def format_directory_result(directory, manifest, kie_versions):
        """Format output for a single directory."""

        return (directory +
                ': ' +
                ('Red Hat manifest ' if 'Red Hat' in manifest else '') +
                'kie-api versions ' +
                '(' + '; '.join(kie_versions) + ')')  # noqa

    directories_for_output = [
        directory
        for directory in base_directories
        if ('Red Hat' in manifest_mfs[directory] or
            kie_versions_by_directory[directory])]
    if kie_versions_by_directory[UNKNOWN_BASE]:
        directories_for_output.append(UNKNOWN_BASE)

    found_redhat_brms = (
        any(('Red Hat' in manifest
             for _, manifest in utilities.iteritems(manifest_mfs))) or
        any((version
             for _, version
             in utilities.iteritems(kie_versions_by_directory))))

    return {JBOSS_BRMS:
            '; '.join(
                [format_directory_result(
                    directory,
                    manifest_mfs[directory],
                    kie_versions_by_directory[directory])
                 for directory in directories_for_output] +
                list(kie_files)),
            JBOSS_BRMS_SUMMARY:
            ('Yes - BRMS installation present'
             if found_redhat_brms else 'No BRMS installation detected')}


JBOSS_FUSE_SUMMARY = 'jboss.fuse.summary'


def generate_fuse_summary(facts_to_collect, facts):
    """Generate a single summary fact about whether the machine has Fuse."""

    if JBOSS_FUSE_SUMMARY not in facts_to_collect:
        return {}

    fuse_on_eap = facts.get(JBOSS_FUSE_FUSE_ON_EAP + MR)
    fuse_on_karaf = facts.get(JBOSS_FUSE_ON_KARAF_KARAF_HOME + MR)
    fuse_init_files = facts.get(JBOSS_FUSE_INIT_FILES + MR)

    if fuse_on_eap or fuse_on_karaf:
        return {JBOSS_FUSE_SUMMARY: 'Yes, Fuse installation present'}

    if fuse_init_files:
        return {JBOSS_FUSE_SUMMARY:
                'Maybe - a Fuse installation might be present'}

    return {JBOSS_FUSE_SUMMARY: 'No Fuse installation detected'}


def escape_characters(data):
    """ Processes input data values and strips out any newlines or commas
    """
    for key in data:
        if utilities.is_stringlike(data[key]):
            value = data[key].replace('\r\n', ' ').replace(',', ' ')
            try:
                data[key] = value.encode('unicode_escape')
            except UnicodeEncodeError:
                data[key] = ''
    return data


# pylint: disable=no-self-use
def determine_pkg_facts(rh_packages):
    """Gets the last installed and last build packages from the list

    :param rh_packages: the filtered list of red hat packages
    :returns: tuple of last installed and last built
    """
    last_installed = None
    last_built = None
    max_install_time = float("-inf")
    max_build_time = float("-inf")
    is_red_hat = 'Y' if rh_packages else 'N'

    for pkg in rh_packages:
        if pkg.install_time > max_install_time:
            max_install_time = pkg.install_time
            last_installed = pkg
        if pkg.build_time > max_build_time:
            max_build_time = pkg.build_time
            last_built = pkg

    last_installed_val = (last_installed.details_install()
                          if last_installed else 'none')
    last_built_val = (last_built.details_built() if last_built else 'none')
    return is_red_hat, last_installed_val, last_built_val


# pylint: disable=too-many-locals, too-many-branches, too-many-statements
def handle_redhat_packages(facts, data):
    """ Process the output of redhat-packages.results
    and supply the appropriate output information
    """
    if 'redhat-packages.results' not in data:
        return

    rhpkg_prefix = 'redhat-packages.'
    gpg_prefix = rhpkg_prefix + 'gpg.'
    gpg_is_rhpkg_str = gpg_prefix + 'is_redhat'
    gpg_num_rh_str = gpg_prefix + 'num_rh_packages'
    gpg_installed_pkg_str = gpg_prefix + 'num_installed_packages'
    gpg_last_installed_str = gpg_prefix + 'last_installed'
    gpg_last_built_str = gpg_prefix + 'last_built'
    gpg_is_rhpkg_in_facts = gpg_is_rhpkg_str in facts
    gpg_num_rh_in_facts = gpg_num_rh_str in facts
    gpg_installed_pkg_in_facts = gpg_installed_pkg_str in facts
    gpg_last_installed_in_facts = gpg_last_installed_str in facts
    gpg_last_built_in_facts = gpg_last_built_str in facts
    installed_packages = None
    try:
        installed_packages = [PkgInfo(line, "|")
                              for line in data['redhat-packages.results']]
    except PkgInfoParseException:
        # facts are already initialized as empty strings
        # just remove the results field
        del data['redhat-packages.results']
        return data

    rh_gpg_packages = list(filter(PkgInfo.is_gpg_red_hat_pkg,
                                  installed_packages))

    if gpg_installed_pkg_in_facts:
        data[gpg_installed_pkg_str] = (len(installed_packages))
    if gpg_num_rh_in_facts:
        data[gpg_num_rh_str] = len(rh_gpg_packages)

    if rh_gpg_packages:
        is_red_hat, last_installed, last_built = \
            determine_pkg_facts(rh_gpg_packages)
        if gpg_is_rhpkg_in_facts:
            data[gpg_is_rhpkg_str] = is_red_hat
        if gpg_last_installed_in_facts:
            data[gpg_last_installed_str] = last_installed
        if gpg_last_built_in_facts:
            data[gpg_last_built_str] = last_built

    del data['redhat-packages.results']


# pylint: disable=too-many-instance-attributes
class PkgInfo(object):
    """This is an inner class for RedhatPackagesRhoCmd
    class and provides functionality to parse the
    results of running the (only) command string
    named 'get_package_info'. This is purely to
    make the parsing cleaner and understandable.
    """
    RED_HAT_KEYS = ('199e2f91fd431d51', '5326810137017186',
                    '45689c882fa658e0', '219180cddb42a60e',
                    '7514f77d8366b0d9', '45689c882fa658e0')

    def __init__(self, row, separator):
        cols = row.split(separator)
        if len(cols) < 14:
            raise PkgInfoParseException()
        else:
            self.name = cols[0]
            self.version = cols[1]
            self.release = cols[2]
            self.install_time = long(cols[3])
            self.vendor = cols[4]
            self.build_time = long(cols[5])
            self.build_host = cols[6]
            self.source_rpm = cols[7]
            self.license = cols[8]
            self.packager = cols[9]
            self.install_date = cols[10]
            self.build_date = cols[11]
            self.is_red_hat = False
            if ('redhat.com' in self.build_host and
                    'fedora' not in self.build_host and
                    'rhndev' not in self.build_host):
                self.is_red_hat = True
            gpgkeys = (cols[12], cols[13], cols[14], cols[15])
            self.is_red_hat_gpg = False
            for known_key in self.RED_HAT_KEYS:
                for rpm_gpg_key in gpgkeys:
                    if known_key in rpm_gpg_key:
                        self.is_red_hat_gpg = True
                        break
                if self.is_red_hat_gpg:
                    break

            # Helper methods to help with recording data in
            # requested fields.

    def is_red_hat_pkg(self):
        """Determines if package is a Red Hat package.
        :returns: True if Red Hat, False otherwise
        """
        return self.is_red_hat

    def is_gpg_red_hat_pkg(self):
        """Determines if package is a Red Hat package with known GPG key.
        :returns: True if Red Hat, False otherwise
        """
        return self.is_red_hat and self.is_red_hat_gpg

    def details_built(self):
        """Provides information on when the package was built
        :returns: String including details and build date
        """
        return "%s Built: %s" % (self.details(), self.build_date)

    def details_install(self):
        """Provides information on when the package was installed.
        :returns: String including installation date
        """
        return "%s Installed: %s" % (self.details(), self.install_date)

    def details(self):
        """Provides package details including name, version and release.
        :returns: String including name, version and release
        """
        return "%s-%s-%s" % (self.name, self.version, self.release)


class PkgInfoParseException(BaseException):
    """Defining an exception for failing to parse package information
    """
    pass


def handle_systemid(fact_names, data):
    """Process the output of systemid.contents
    and supply the appropriate output information
    """
    if 'systemid.contents' in data:
        blob = data['systemid.contents']
        id_in_facts = 'SysId_systemid.system_id' in fact_names
        username_in_facts = 'SysId_systemid.username' in fact_names
        try:
            systemid = xmlrpclib.loads(blob)[0][0]
            if id_in_facts and 'system_id'in systemid:
                data['systemid.system_id'] = systemid['system_id']
            if username_in_facts and 'usnername' in systemid:
                data['systemid.username'] = systemid['usnername']
        except xml.parsers.expat.ExpatError:
            if id_in_facts:
                data['systemid.system_id'] = 'error'
            if username_in_facts:
                data['systemid.username'] = 'error'

        del data['systemid.contents']
    return data
