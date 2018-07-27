#! /usr/bin/python
'''This module verifies the previously run role variables against system information.'''

import subprocess

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils import facts

ANSIBLE_METEDATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: role_test
short_description: Verify that the previous run role matches system information.
version_added: "2.6"
description:
    - "Module uses the same parameters as the previous run role, and runs various
    tests depending on the values of the state and device_type variables"
options:
    - See https://github.com/dwlehman/linux-storage-role for usage of variables
author:
    - Tim Flannagan (tflannag@redhat.com)
'''

EXAMPLES = '''
- include_role:
    name: ../linux-storage-role
  vars:
    device_name: 'test1'
    disks: ['vdb']
    lvm_vg: 'rhel_ibm'
    mount_point: '/opt/test1'
    size: '13g'

- name: Check test1 results 
  role_test:
    device_name: 'test1'
    disks: ['vdb']
    lvm_vg: 'rhel_ibm'
    mount_point: '/opt/test1'
    size: '13g'
  register: test1_results 

- include_role:
    name: ../linux-storage-role
  vars:
    device_type: 'disk'
    mount_point: '/opt/test2'
    disks: ['vdc']

- name: Check test2 results 
  role_test:
    device_type: 'disk'
    disks: ['vdc']
    mount_point: '/opt/test2'
  register: test2_results
'''

RETURN = '''
num_tests:
    description: The number of main tests used to verify role information"
    type: int

num_successes:
    descrption: The number of successful tests run
    type: int

failed_tests:
    description: A list of failed tests with error/debugging messages
    type: list
'''

def verify_absent_fstab_info(role_dict, failed_tests):
    '''Check if the info specified in the role_dict is absent in the /etc/fstab file.'''
    found_line = False
    implemented = True

    if not implemented:
        failed_tests.append('Check failed as verify_absent_fstab_info has not been implemented.')
        return True

    if role_dict['device_type'] is not None and role_dict['device_type'] in 'disk':
        expected_name = '/dev/' + role_dict['disks'][0]
    else:
        expected_name = '/dev/mapper/' + role_dict['lvm_vg'] + '-' + role_dict['device_name']

    with open('/etc/fstab', 'r') as file_buf:
        for line in file_buf.readlines():
            if expected_name in line:
                found_line = True
                break

    if found_line:
        failed_tests.append('Check failed as there is still info about device in /etc/fstab file.')
        return True

    return False

def absent_disk_helper(role_dict, failed_tests):
    '''Verify that the specified disk is unmounted, but present in lsblk output.'''
    expected_name = '/dev/' + role_dict['disks'][0]

    lsblk_cmd = "lsblk %s -o name,fstype,mountpoint --noheadings" % expected_name
    lsblk_buf = subprocess.check_output(lsblk_cmd, shell=True).split()

    if len(lsblk_buf) is not 1:
        failed_tests.append('Debug check: the length of the lsblk buffer is invalid.')
        return True

    if lsblk_buf[0] not in role_dict['disks'][0]:
        failed_tests.append('Check failed as disk is not present in lsblk buffer.')
        return True

    return False

def absent_lvm_helper(role_dict, failed_tests):
    '''Verify that the specified lvm device is not present in lvs command output.'''
    try:
        lvs_cmd = "sudo lvs %s -o name --no-headings" % role_dict['lvm_vg']
        lvs_buf = subprocess.check_output(lvs_cmd, shell=True).replace('\n', '').split()
    except subprocess.CalledProcessError:
        return False

    if role_dict['device_name'] in lvs_buf:
        failed_tests.append('Check failed as device name %s was found in \
            lvs output when run in absent state.' % role_dict['device_name'])
        return True

    return False

def verify_absent_mount_info(role_dict, failed_tests):
    '''Run helper functions and return the was_failed flag.'''
    was_failed = False

    if role_dict['device_type'] is not None and role_dict['device_type'] in 'disk':
        was_failed = absent_disk_helper(role_dict, failed_tests)
    else:
        was_failed = absent_lvm_helper(role_dict, failed_tests)

    return was_failed

def verify_absent_state(role_dict, test_run_results):
    '''Driver function that handles verification when state is set as absent.'''
    was_failed = False

    if verify_absent_fstab_info(role_dict, test_run_results['tests_failed']):
        was_failed = True
    else:
        test_run_results['num_successes'] += 1

    if verify_absent_mount_info(role_dict, test_run_results['tests_failed']):
        was_failed = True
    else:
        test_run_results['num_successes'] += 1

    test_run_results['num_tests'] += 2

    return was_failed

def verify_present_default_size(role_dict, failed_tests):
    '''Check if there is any free space left over after using default size.'''
    was_failed = True

    try:
        pvs_cmd = "sudo pvs /dev/%s -o free,size --no-headings --units g" % role_dict['disks'][0]
        pvs_buf = subprocess.check_output(pvs_cmd, shell=True).split()
    except subprocess.CalledProcessError as error_msg:
        failed_tests.append('Error: %s' % error_msg)
        return True

    if len(pvs_buf) < 2:
        failed_tests.append('Check failed as the pvs buffer is not the right size.')
        return True

    free_space = float(pvs_buf[0].replace('g', ''))
    total_size = float(pvs_buf[1].replace('g', ''))

    if (total_size != 0.0) and (free_space != 0.0):
        failed_tests.append('Check failed as there is still \
            free space remaining the pv %s' % role_dict['disks'][0])
        was_failed = True

    return was_failed

def pv_percentage_size(role_dict, failed_tests):
    '''Check if the specified percentage for used pvs matches system info.'''
    was_failed = False

    try:
        lvs_cmd = "sudo lvs %s -o name,size --no-headings --units g" % role_dict['lvm_vg']
        lvs_buf = subprocess.check_output(lvs_cmd, shell=True).split()

        pvs_cmd = "sudo pvs /dev/%s -o vg_name,free,size --no-headings --units g" % role_dict['disks'][0]
        pvs_buf = subprocess.check_output(pvs_cmd, shell=True).split()
    except subprocess.CalledProcessError as error_msg:
        failed_tests.append('Error: %s' % error_msg)
        failed_tests.append('Check failed as the pvs/lvs command did not \
            recognize the lvm vg name (%s) given.' % role_dict['lvm_vg'])
        return True

    if (len(pvs_buf) < 3) or (len(lvs_buf) < 2):
        failed_tests.append('Check failed as the length of the pvs \
            buffer is the required size in % PV.')
        return True

    if role_dict['lvm_vg'] in pvs_buf:
        pvs_index = pvs_buf.index(role_dict['lvm_vg'])
    else:
        failed_tests.append('Check failed as %s is not present in \
            the pvs command output.' % role_dict['lvm_vg'])
        return True

    if (pvs_index + 2) >= len(pvs_buf):
        failed_tests.append('Debug check: something went wrong when \
            the index pulled from the vg name in pvs buffer.')
        return True

    if role_dict['device_name'] in lvs_buf:
        lvs_index = lvs_buf.index(role_dict['device_name'])
    else:
        failed_tests.append('Check failed as %s is not present in the \
            lvs command output.' % role_dict['device_name'])
        return True

    total_pv_size = float(pvs_buf[pvs_index + 2].replace('g', ''))
    free_space = float(pvs_buf[pvs_index + 1].replace('g', ''))
    expected_percentage = float(role_dict['size'].split('%')[0]) * 0.01
    actual_size = float(lvs_buf[lvs_index + 1].replace('g', ''))

    expected_size = total_pv_size * expected_percentage

    if expected_size != actual_size:
        if free_space != 0.0:
            failed_tests.append('Check failed as the expected size and actual \
                size differ (pv): %d -> %d' % (expected_size, actual_size))
            was_failed = True

    return was_failed

def vg_percentage_size(role_dict, failed_tests):
    '''Check if the specified percentage of VG was used against system info. '''
    was_failed = False

    try:
        vgs_cmd = "sudo vgs %s -o free,size --no-headings --units g" % role_dict['lvm_vg']
        vgs_buf = subprocess.check_output(vgs_cmd, shell=True).split()

        lvs_cmd = "sudo lvs %s -o name,size --no-headings --units g" % role_dict['lvm_vg']
        lvs_buf = subprocess.check_output(lvs_cmd, shell=True).split()
    except subprocess.CalledProcessError as error_msg:
        failed_tests.append('Error: %s' % error_msg)
        failed_tests.append('Check failed as the vgs/lvs command \
            did not recognize the lvm vg name given.')
        return True

    if len(vgs_buf) is not 2 or len(lvs_buf) < 2:
        failed_tests.append('Check failed as the vgs command output \
            does not meet the required length.')
        return True

    if role_dict['device_name'] in lvs_buf:
        index = lvs_buf.index(role_dict['device_name'])
    else:
        failed_tests.append('Check failed as the device name (%s) \
            was not found in the lvs buffer.' % role_dict['device_name'])
        return True

    total_size = float(vgs_buf[1].replace('g', ''))
    actual_size = float(lvs_buf[index + 1].replace('g', ''))
    remaining_space = float(vgs_buf[1].replace('g', ''))
    expected_percentage = float(role_dict['size'].split('%')[0]) * 0.01

    expected_size = expected_percentage * total_size

    if expected_size != actual_size:
        if remaining_space != 0.0:
            failed_tests.append('Check failed as the expected and \
                actual sizes differ: %f -> %f' % (expected_size, actual_size))
            was_failed = True

    return was_failed

def verify_present_percentage_size(role_dict, failed_tests):
    '''Verify the percentage in the size parameter matches up the size in the system.'''
    was_failed = False

    if 'VG' in role_dict['size']:
        was_failed = vg_percentage_size(role_dict, failed_tests)
    elif 'PVS' in role_dict['size']:
        was_failed = pv_percentage_size(role_dict, failed_tests)
    else:
        failed_tests.append('Check failed as this module has no way to test %FREE atm.')
        was_failed = True

    return was_failed

def verify_present_specified_size(device_name, lvm_vg_name, size, failed_tests):
    '''Check if the role variables match the info presented in lvs command output.'''
    was_failed = False

    try:
        lvs_cmd = "sudo lvs %s -o name,size --no-headings --units g" % lvm_vg_name
        lvs_buf = subprocess.check_output(lvs_cmd, shell=True).split()
    except subprocess.CalledProcessError as error_msg:
        failed_tests.append('Error: %s' % error_msg)
        failed_tests.append('Check failed as the lvs command \
            did not recognize the lvm vg name given.')
        return True

    if len(lvs_buf) < 2:
        failed_tests.append('Check failed as lvs command failed \
            to output correct fields in specified_value.')
        return True

    if device_name in lvs_buf:
        index = lvs_buf.index(device_name)
    else:
        failed_tests.append('Check failed as the device name \
            (%s) was not present in the lvs command output.' % device_name)
        return True

    if (index + 1) >= len(lvs_buf):
        failed_tests.append('Debug: something went wrong in the lvs output grab.')
        return True

    index += 1
    size = float(size.replace('g', ''))
    lvs_buf[index] = float(lvs_buf[index].replace('g', ''))

    if lvs_buf[index] != size:
        failed_tests.append('Check failed as the size parameter \
            and size listed in lvs command differ: %f -> %f' % (lvs_buf[index], size))
        was_failed = True

    return was_failed

def verify_present_size(role_dict, failed_tests):
    '''Check the format of the size variable in role_dict, and call the corresponding functions.'''
    was_failed = False

    if role_dict['size'] is None or role_dict['size'] in '100%FREE':
        was_failed = verify_present_default_size(role_dict, failed_tests)
    elif role_dict['size'] is not None and '%' in role_dict['size']:
        was_failed = verify_present_percentage_size(role_dict, failed_tests)
    else:
        was_failed = verify_present_specified_size(role_dict['device_name'], \
            role_dict['lvm_vg'], role_dict['size'], failed_tests)

    return was_failed

def verify_present_fstab_info(role_dict, failed_tests):
    '''Verify the device info by reading the /etc/fstab file and pulling out relevant data.'''
    was_failed = False
    device_was_found = True
    line_buf = []

    if role_dict['device_type'] is not None and role_dict['device_type'] in 'disk':
        device = role_dict['disks'][0]
        expected_name = '/dev/' + role_dict['disks'][0]
    else:
        device = role_dict['device_name']
        expected_name = '/dev/mapper/' + role_dict['lvm_vg'] + '-' + role_dict['device_name']

    with open('/etc/fstab', 'r') as file_buf:
        for line in file_buf.readlines():
            if expected_name in line:
                device_was_found = True
                line_buf = line.split()
                break

    if not device_was_found:
        failed_tests.append('Check failed as the specified device (%s) \
            was not found in the /etc/fstab file.' % device)
        return True

    if len(line_buf) is not 6:
        failed_tests.append('Debug check: the length of the returned line \
            buffer in /etc/fstab does not meet the required length.')
        return True

    # Check that the correct fs type is on the specified disk
    if role_dict['fs_type'] is None:
        if 'xfs' not in line_buf:
            failed_tests.append('Check failed as default file system type \
                was specified, but /etc/fstab file has differing fs type.')
            was_failed = True
    else:
        if role_dict['fs_type'] not in line_buf:
            failed_tests.append('Check failed as /etc/fstab file has differing \
                fs types: %s -> %s' % (role_dict['fs_type'], line_buf[2]))
            was_failed = True

    if role_dict['mount_point'] not in line_buf:
        failed_tests.append('Check failed as the specified mount point (%s) \
            does not match the mount (%s) in /etc/fstab file.' % \
            (role_dict['mount_point'], line_buf[1]))
        was_failed = True

    return was_failed

def verify_present_lsblk_info(role_dict, failed_tests):
    '''Check the variables initialized in the role_dict against lsblk command output.'''
    was_failed = False

    if role_dict['device_type'] is not None and role_dict['device_type'] in 'disk':
        device = role_dict['disks'][0]
        expected_name = '/dev/' + role_dict['disks'][0]
    else:
        device = role_dict['lvm_vg'] + '-' + role_dict['device_name']
        expected_name = '/dev/mapper/' + role_dict['lvm_vg'] + '-' + role_dict['device_name']

    try:
        lsblk_cmd = "lsblk %s -o name,fstype,mountpoint --noheadings" % expected_name
        lsblk_buf = subprocess.check_output(lsblk_cmd, shell=True).split()
    except subprocess.CalledProcessError as error_msg:
        failed_tests.append('Error: %s' % error_msg)
        failed_tests.append('Check failed as lsblk was not able \
            to return the device %s.' % expected_name)
        return True

    if len(lsblk_buf) is not 3:
        failed_tests.append('Check failed as the length of the lsblk \
            buffer was the required length.')
        return True

    if device not in lsblk_buf[0]:
        failed_tests.append('Check failed as the device %s was not found \
            in the lsblk buffer.' % device)
        was_failed = True

    if role_dict['fs_type'] is None or role_dict['fs_type'] in 'xfs':
        if lsblk_buf[1] not in 'xfs':
            failed_tests.append('Check failed as the fs type in the role \
                differs from the type in lsblk: %s -> %s' % ('xfs', lsblk_buf[1]))
            was_failed = True

    if role_dict['mount_point'] not in lsblk_buf[2]:
        failed_tests.append('Check failed as the mount point defined the \
            role does not match the mount point in lsblk: %s -> %s \
                ' % (role_dict['mount_point'], lsblk_buf[3]))
        was_failed = True

    return was_failed

def verify_present_state(role_dict, test_run_results):
    '''Driver function that handles verification when state is set as present.'''
    was_failed = False

    if verify_present_size(role_dict, test_run_results['tests_failed']):
        was_failed = True
    else:
        test_run_results['num_successes'] += 1

    if verify_present_fstab_info(role_dict, test_run_results['tests_failed']):
        was_failed = True
    else:
        test_run_results['num_successes'] += 1

    if verify_present_lsblk_info(role_dict, test_run_results['tests_failed']):
        was_failed = True
    else:
        test_run_results['num_successes'] += 1

    test_run_results['num_tests'] += 3

    return was_failed

def is_invalid(role_dict, failed_list):
    '''Check that the .yml file uses the correct fields before running verification functions.'''
    was_failed = False

    if role_dict['device_type'] is 'disk':
        if len(role_dict['disks']) > 1:
            failed_list.append('Check failed as device type is "disk" \
                and user entered more than one disk.')
            was_failed = True

        if role_dict['lvm_vg'] is not None:
            failed_list.append('Check failed as device type is "disk" \
                and user supplied a name for lvm_vg.')
            was_failed = True

        if role_dict['device_name'] is not None:
            failed_list.append('Check failed as device type is "disk" \
                and user supplied a name for device_name.')
            was_failed = True
    if (role_dict['size'] is not None) and ('+' in role_dict['size']):
        failed_list.append('Check failed as user entered extended \
            size option, but that is not supported yet.')
        was_failed = True

    return was_failed

def run_module():
    module_args = dict(
        device_type=dict(type='str'),
        device_name=dict(type='str'),
        disks=dict(type='list', required='True'),
        size=dict(type='str'),
        fs_type=dict(type='str'),
        fs_label=dict(type='str'),
        fs_create_options=dict(type='str'),
        mount_point=dict(type='str', required='True'),
        mount_options=dict(type='str'),
        lvm_vg=dict(type='str'),
        state=dict(type='str')
    )
    # Will probably change as this module develops more
    results = dict(
        num_tests=0,
        num_successes=0,
        tests_failed=[],
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Do all the policing of the .yml file first
    if is_invalid(module.params, results['tests_failed']):
        module.exit_json(msg='Invalid: {}').format(results['tests_failed'])

    if module.params['state'] is None or module.params['state'] in 'present':
        test_failed = verify_present_state(module.params, results)
    else:
        test_failed = verify_absent_state(module.params, results)

    if not test_failed:
        module.exit_json(**results)
    else:
        module.exit_json(msg='Failed: {}'.format(results['tests_failed']))

def main():
    run_module()

if __name__ == '__main__':
    main()
