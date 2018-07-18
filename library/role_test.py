#! /usr/bin/python

'''
- Info about role variables: https://github.com/dwlehman/linux-storage-role/tree/initial-docs
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils import facts
import subprocess

# Both LVM and disk device types will have mounted file systems
# def verify_fs_type(module_params):
#     xfs_type = False
#     lvm_device = False
#     rval = False
#
#     # Steps:
#     # 1. Check whether device type is None (default is lvm)
#     #    a. Default: Need to know device name, check against its fs type in /etc/fstab
#     #    b. Other: Need to check the disks against its mounted fs type
#     # 2. Check whether expected_fs_type is None (default is xfs)
#
#     if module_params['device_type'] is not None:
#         lsblk_cmd = "lsblk -fi | grep %s | awk '{ print $1, $2 }'" % module_params['device_name']
#     else:
#         # This is a stub atm
#         lvm_device = True
#         # lsblk_cmd = "lsblk -fi | grep %s | awk '{ print $1, $2 }'" % module_params['disks']
#
#     lsblk_buf = subprocess.check_output(lsblk_cmd, shell=True)
#
#     if not lvm_device:
#         lsblk_buf = lsblk_buf.split()
#     else:
#         # We know this is an lvm device, so we need to be careful in parsing the input
#         lsblk_buf = lsblk_buf.replace('|-', '').split()
#
#         # Now we need to check if the file system type
#         if module_params['fs_type'] is not None:
#             if not module_params['device_name'] in lsblk_buf[0] or not module_params['fs_type'] in lsblk_buf[1]:
#                 # Eventually add some way to use error messages
#                 rval = False
#
#         # lsblk_buf[0] = device_name, lsblk_buf[1] = file system type
#
#
#     return True

# def initialize_expected_results(module_params):
#     fail_flag = False
#     tests_failed = []
#     num_successes = 0
#     num_tests = 1
#
#     if not verify_fs_type(module_params['fs_type']):
#         tests_failed.append('Verify File System Type')
#         fail_flag = True
#     else:
#         num_successes += 1
#
#     return tests_failed, num_successes, num_tests

def verify_mount(role_variables, fail_reasons):
	is_default = False
	failed = False

	if role_variables['fs_type'] is None:
		role_variables['fs_type'] = 'xfs'

	if role_variables['device_type'] is None:
		is_default = True 

		try:
			lsblk_cmd = "lsblk -fi | grep %s | awk '{ print $1, $2, $4 }'" % role_variables['device_name']
		except: 
			fail_reasons.append('Subprocess command failed in verify_mount function. It is possible the device name is not defined: %s' % role_variables['device_name'])
			return False
	else:
		lsblk_cmd = "lsblk -fi | grep %s | awk '{ print $1, $2, $4 }'" % role_variables['disks[0]']

	lsblk_buf = subprocess.check_output(lsblk_cmd, shell=True)

	if is_default:
		lsblk_buf = lsblk_buf.replace('|-', '').replace("'-", "").split()
		expected_name = role_variables['lvm_vg'] + '-' + role_variables['device_name']
 
		if not expected_name in lsblk_buf[0]:
			fail_reasons.append('Check failed with differing expected device name in lsblk output: %s -> %s' % (expected_name, lsblk_buf[0]))
			failed = True

		if not role_variables['fs_type'] in lsblk_buf[1]:
			fail_reasons.append('Check failed with differing fs types: %s -> %s' % (role_variables['fs_type'], lsblk_buf[1]))
			failed = True

		if not role_variables['mount_point'] in lsblk_buf[2]:
			fail_reasons.append('Check failed with differing mount points: %s -> %s' % (role_variables['mount_point'], lsblk_buf[2]))
			failed = True
	else:
		fail_reasons.append('Somehow this passed with %s -> %d' % (role_variables['device_type']), is_default)

	return failed

def verify_fs_type(role_variables, fail_reasons):
	fail_reasons.append('This is a stub')
	return True

def test_absent_status(role_variables, results):
    '''Test driver for absent status: return False is no tests failed'''
    return True

def test_present_status(role_variables, results):
    '''Test driver for present status: return False is no tests failed'''
    failed = False

    if verify_fs_type(role_variables, results['tests_failed']):
    	failed = True
    else:
    	results['num_successes'] += 1

    if verify_mount(role_variables, results['tests_failed']):
    	failed = True 
    else:
    	results['num_successes'] += 1

    # Probably need to reword these variables at some point
    return failed

def run_module():
    '''Setup and initialize all relevant ansible module data'''
    module_args = dict(
        device_type         = dict(type='str'),
        device_name         = dict(type='str'),
        disks               = dict(type='str', required='True'),
        size                = dict(type='str'),
        fs_type             = dict(type='str'),
        fs_label            = dict(type='str'),
        fs_create_options   = dict(type='str'),
        mount_point         = dict(type='str', required='True'),
        mount_options       = dict(type='str'),
        lvm_vg              = dict(type='str'),
        status              = dict(type='str')
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

    # Note: present status (default) is going to build up the specified device variables
    if module.params['status'] is not None:
        tests_failed = test_absent_status(module.params, results)
    else:
        tests_failed = test_present_status(module.params, results)

    if not tests_failed:
        module.exit_json(**results)
    else:
        module.fail_json(msg="{}".format(results['tests_failed']))

def main():
    run_module()

if __name__ == '__main__':
    main()
