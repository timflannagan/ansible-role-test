#! /usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils import facts
import subprocess

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

    with open('/etc/fstab', 'r') as file:
        for line in file.readlines():
            if expected_name in line:
                found_line = True
                break

    if found_line:
        failed_tests.append('Check failed as there is still info about device in /etc/fstab file.')
        return True

def absent_disk_helper(role_dict, failed_tests):
    '''Helper function for verifying that specified disk is unmounted, but present in lsblk output.'''
    expected_name = '/dev/' + role_dict['disks'][0]

    lsblk_cmd = "lsblk %s -o name,fstype,mountpoint --noheadings" % expected_name
    lsblk_buf = subprocess.check_output(lsblk_cmd, shell=True).split()

    if len(lsblk_buf) is not 1:
        failed_tests.append('Debug: lsblk command failed to return required number of fields (most likely incorrect syntax in .yml file).')
        return True

    if lsblk_buf[0] not in role_dict['disks'][0]:
        failed_tests.append('Check failed as the name of the disk specified in the .yml file does not match the lsblk output.')
        return True

def absent_lvm_helper(role_dict, failed_tests):
    '''Helper function for verifying that specified lvm device is not present in lvs command output.'''
    try:
        lvs_cmd = "sudo lvs %s -o name --no-headings" % role_dict['lvm_vg']
        lvs_buf = subprocess.check_output(lvs_cmd, shell=True).replace('\n', '').split()
    except subprocess.CalledProcessError as e:
        return False

    if role_dict['device_name'] in lvs_buf:
        failed_tests.append('Check failed as device name %s was found in lvs output when run in absent state.' % role_dict['device_name'])
        return True

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
	return True

def verify_present_percentage_size(role_dict, failed_tests):
	return True

def verify_present_specified_size(role_dict, failed_tests):
	return True

def verify_present_size(role_dict, failed_tests):
	'''Check the format of the size variable in role_dict, and call the corresponding verification function.'''
	was_failed = False

	if role_dict['size'] is None or role_dict['size'] in '100%FREE':
		was_failed = verify_present_default_size(role_dict, failed_tests)
	else if role_dict['size'] is not None and '%' in role_dict['size']:
		was_failed = verify_present_percentage_size(role_dict, failed_tests)
	else:
		was_failed = verify_present_specified_size(role_dict, failed_tests)

	return was_failed

def verify_present_state(role_dict, test_run_results):
    '''Driver function that handles verification when state is set as present.'''
    was_failed = False
    implemented = False

    if not implemented:
        test_run_results['tests_failed'].append('Check failed as verify_present_state is not yet implemented.')
        return True

    if verify_present_size(role_dict, test_run_results['tests_failed']):
    	was_failed = True
    else:
    	tests_run_results['num_successes'] += 1

    return was_failed

def is_invalid(role_dict, failed_list):
    '''Check that the .yml file uses the correct fields before running verification functions.'''
    was_failed = False

    if role_dict['device_type'] is 'disk':
        if len(role_dict['disks']) > 1:
            failed_list.append('Check failed as device type is "disk" and user entered more than one disk.')
            was_failed = True

        if role_dict['lvm_vg'] is not None:
            failed_list.append('Check failed as device type is "disk" and user supplied a name for lvm_vg.')
            was_failed = True

        if role_dict['device_name'] is not None:
            failed_list.append('Check failed as device type is "disk" and user supplied a name for device_name.')
            was_failed = True

    if (role_dict['size'] is not None) and ('+' in role_dict['size']):
        failed_list.append('Check failed as user entered extended size option, but that is not supported yet.')
        was_failed = True

    return was_failed

def run_module():
    module_args = dict(
        device_type         = dict(type='str'),
        device_name         = dict(type='str'),
        disks               = dict(type='list', required='True'),
        size                = dict(type='str'),
        fs_type             = dict(type='str'),
        fs_label            = dict(type='str'),
        fs_create_options   = dict(type='str'),
        mount_point         = dict(type='str', required='True'),
        mount_options       = dict(type='str'),
        lvm_vg              = dict(type='str'),
        state               = dict(type='str')
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