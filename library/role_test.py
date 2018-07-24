#! /usr/bin/python

'''
- Info about role variables: https://github.com/dwlehman/linux-storage-role/tree/initial-docs
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils import facts
import subprocess

def verify_lvm_mount(role_variables, lsblk_buf, fail_reasons):
	lsblk_buf = lsblk_buf.replace('|-', '').replace("'-", "").split()
	expected_name = role_variables['lvm_vg'] + '-' + role_variables['device_name']
	failed = False

	if len(lsblk_buf) is not 3:
		fail_reasons.append('Grep/awk was unable to return all three fields. Device name is most likely invalid')
		return True 

	if not expected_name in lsblk_buf[0]:
		fail_reasons.append('Check failed with differing expected device name in lsblk output: %s -> %s' % (expected_name, lsblk_buf[0]))
		failed = True

	if not role_variables['fs_type'] in lsblk_buf[1]:
		fail_reasons.append('Check failed with differing fs types: %s -> %s' % (role_variables['fs_type'], lsblk_buf[1]))
		failed = True

	if not role_variables['mount_point'] in lsblk_buf[2]:
		fail_reasons.append('Check failed with differing mount points: %s -> %s' % (role_variables['mount_point'], lsblk_buf[2]))
		failed = True

	return failed

def verify_disk_mount(role_variables, lsblk_buf, fail_reasons):
	lsblk_buf = lsblk_buf.replace('\n', '').split()
	failed = False 

	if len(lsblk_buf) is not 3:
		fail_reasons.append('Grep/awk was unable to return all three fields in verify_disk_mount. The first disk in the list was likely invalid')
		return True

	if not role_variables['disks'][0] in lsblk_buf[0]:
		fail_reasons.append('Check failed with different for disks: %s -> %s' % (role_variables['disks'][0], lsblk_buf[0]))
		failed = True

	if not role_variables['fs_type'] in lsblk_buf[1]:
		fail_reasons.append('Check failed with differing fs types in lsblk: %s -> %s' % (role_variables['fs_type'], lsblk_buf[1])) 
		failed = True

	if not role_variables['mount_point'] in lsblk_buf[2]:
		fail_reasons.append('Check failed with differing mount points in lsblk: %s -> %s' % (role_variables['mount_point'], lsblk_buf[2]))
		failed = True

	return failed

def verify_mount(role_variables, fail_reasons):
	'''Function executes a lsblk command and checks role variables against parsed lsblk output'''
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
		lsblk_cmd = "lsblk -fi | grep %s | awk '{ print $1, $2, $4 }'" % role_variables['disks'][0]

	lsblk_buf = subprocess.check_output(lsblk_cmd, shell=True)

	if is_default:
		failed = verify_lvm_mount(role_variables, lsblk_buf, fail_reasons)
	else:
		failed = verify_disk_mount(role_variables, lsblk_buf, fail_reasons)

	return failed

def verify_lvm_fs_type(role_variables, fail_reasons):
	failed = False 

	try:
		expected_name = '/dev/mapper/' + role_variables['lvm_vg'] + '-' + role_variables['device_name']
	except:
		fail_reasons.append('Either the lvm_vg field is NoneType or device_name field is NoneType')
		return True 

	cat_cmd = "cat /etc/fstab | grep %s | awk '{ print $1, $2, $3 }'" % expected_name
	cat_buf = subprocess.check_output(cat_cmd, shell=True).replace('\n', '').split()

	if not expected_name in cat_buf[0]:
		fail_reasons.append('%s-%s was not found in fstab name column: %s' % (role_variables['lvm_vg'], role_variables['device_name'], cat_buf[0]))
		failed = True

	if not role_variables['mount_point'] in cat_buf[1]:
		fail_reasons.append('Check failed with differing mount points in fstab file: %s -> %s' % (role_variables['mount_point'], cat_buf[1]))

	if not role_variables['fs_type'] in cat_buf[2]:
		fail_reasons.append('Check failed with differing file system types in fstab file: %s -> %s' % (role_variables['fs_type'], cat_buf[2]))
		failed = True

	return failed 

def verify_disk_fs_type(role_variables, fail_reasons):
	failed = False 

	for disk in role_variables['disks']:
		expected_name = '/dev/' + disk

		cat_cmd = "cat /etc/fstab | grep %s | awk '{ print $1, $2, $3 }'" % expected_name 
		cat_buf = subprocess.check_output(cat_cmd, shell=True).replace('\n', '').split()

		if len(cat_buf) is not 3:
			fail_reasons.append('Grep/awk command failed to produce all three fields in verify_disk_fs_type')
			return True 

		# fs_type was defined in the parent function
		if not expected_name in cat_buf[0]:
			fail_reasons.append('Check failed with differing names in fstab file: %s -> %s in disk %d' % (expected_name, cat_buf[0]), disk)
			failed = True 

		if not role_variables['mount_point'] in cat_buf[1]:
			fail_reasons.append('Check failed with differing mount points in fstab file: %s -> %s in disk %d' % (role_variables['mount_point'], cat_buf[1]), disk)
			failed = True 

		if not role_variables['fs_type'] in cat_buf[2]:
			fail_reasons.append('Check failed with differing fs types in fstab file: %s -> %s in disk %d' % (role_variables['fs_type'], cat_buf[2], disk))
			failed = True 

	return failed 

def verify_fs_type(role_variables, fail_reasons):
	'''Function verifies info located in /etc/fstab file against the expected role variables'''
	failed = False

	if role_variables['fs_type'] is None:
		role_variables['fs_type'] = 'xfs'

	if role_variables['device_type'] is None:
		failed = verify_lvm_fs_type(role_variables, fail_reasons)
	else:
		failed = verify_disk_fs_type(role_variables, fail_reasons)

	return failed

def verify_other_logical_volumes(role_variables, fail_reasons):
	failed = False 
	fail_reasons.append('Check failed as this is not implemented yet.')
	return failed

def verify_free_size_percentage(role_variables, fail_reasons):
	failed = False
	implemented = True

	if not implemented:
		fail_reasons.append('Check failed as %FREE size has not been added to the verification function.')
		return True

	if len(role_variables['disks']) is not 0:
		# Need to calculate the before and after the logical volume had been mounted
		expected_name = '/dev/' + role_variables['disks'][0]

		pvs_cmd = "sudo pvs %s --no-headings | awk '{ print $5, $6 }'" % expected_name
		pvs_buf = subprocess.check_output(pvs_cmd, shell=True).split()

		# pvs_buf[0] = total size, pvs_buf[1] = total_free
		if len(pvs_buf) is not 2:
			fail_reasons.append('Check failed as the length of the pvs output is less than the expected length.')
			return True 

		# Initialize necessary variables
		expected_percentage = float(role_variables['size'].split('%')[0]) * 0.01
		total_space = float(pvs_buf[0].replace('<', '').replace('g', '').replace('m', ''))
		remaining_space = float(pvs_buf[1].replace('<', '').replace('g', '').replace('m', ''))
		
		debug_value = int(role_variables['size'].split('%')[0]) + (expected_percentage * total_space)

		if debug_value != total_space:
			failed = verify_other_logical_volumes(role_variables, fail_reasons)
			# fail_reasons.append('DEBUG: %s (theres probably more LVs on the disk %s' % (debug_value, expected_name))
			# failed = True

	else:
		fail_reasons.append('Check failed as user entered an empty disks list (not sure how to handle this atm.)')
		failed = True


	return failed

def verify_size_percentage(role_variables, fail_reasons):
	failed = False 

	if 'FREE' in role_variables['size']:
		failed = verify_free_size_percentage(role_variables, fail_reasons)		
	elif 'VG' in role_variables['size']:
		fail_reasons.append('Check failed as %VG of the verify_size_percentage function has not been implemented yet.')
		failed = True
	elif 'PVS' in role_variables['size']:
		fail_reasons.append('Check failed as %PVS of the verify_size_percentage function has not been implemented yet.')
		failed = True
	else:
		fail_reasons.append('Check failed as user must have inputted an incorrect format for size. [FREE|VG|PV]')
		failed = True

	return failed 

def verify_size(role_variables, fail_reasons):
	'''Check if lvm device has correct size'''
	failed = False 

	if role_variables['device_type'] is not None:
		return False 

	if role_variables['size'] is None or role_variables['size'] in '100%FREE':
		vgs_cmd = "sudo vgs | grep -w %s | awk '{ print $7 }'" % role_variables['lvm_vg']
		vgs_buf = subprocess.check_output(vgs_cmd, shell=True).split()

		if len(vgs_buf) is not 1:
			fail_reasons.append('Something was inputted wrong in the site.yml file, exiting: %s' % vgs_buf)
			return True

		if not '0' in vgs_buf[0]:
			fail_reasons.append('Check failed as default size was used in lvm creation but there is still space in the vg leftover')
			failed = True
	elif '%' in role_variables['size']:
		failed = verify_size_percentage(role_variables, fail_reasons)		
	else:
		expected_name = role_variables['lvm_vg'] + '-' + role_variables['device_name']
		lsblk_cmd = "lsblk | grep %s | awk '{ print $4 }'" % expected_name
		lsblk_buf = subprocess.check_output(lsblk_cmd, shell=True).replace('|-', '').replace("'-", '').split()

		if len(lsblk_buf) is not 1:
			fail_reasons.append('lsblk/grep command failed to produce the single field in verify_size')
			return True 

		if 'gib' in role_variables['size'].lower():
			role_variables['size'] = role_variables['size'].lower().replace('gib', 'g')

		if 'mib' in role_variables['size'].lower():
			role_variables['size'] = role_variables['size'].lower().replace('mib', 'mb')

		if not role_variables['size'].lower() in lsblk_buf[0].lower():
			fail_reasons.append('Check failed as there are differing sizes in lsblk: %s -> %s' % (role_variables['size'], lsblk_buf[0]))
			failed = True 

	return failed 

def verify_fstab_info(role_variables, fail_reasons):
	'''Check the /etc/fstab info and make sure no disk/lvm device is listed there when state is specified as absent'''
	failed = False 

	if role_variables['device_type'] is not None and role_variables['disks'] in 'disk':
		expected_name = '/dev/' + role_variables['disks'][0]
	else:
		expected_name = '/dev/mapper/' + role_variables['lvm_vg'] + '-' + role_variables['device_name']

	cat_cmd = "cat /etc/fstab | grep %s | awk '{ print $1, $2, $3 }'" % expected_name
	cat_buf = subprocess.check_output(cat_cmd, shell=True).replace('\n', '').split()

	if len(cat_buf) is not 0:
		fail_reasons.append('Check failed as %s is still listed in the /etc/fstab file' % expected_name)
		failed = True

	return failed

def verify_lsblk_mount(role_variables, fail_reasons):
	'''Check if corresponding device type is nonexistent in lsblk command output'''
	failed = False

	if role_variables['device_type'] is not None and role_variables['device_type'] in 'disk':
		expected_name = role_variables['disks'][0]
	else:
		expected_name = role_variables['lvm_vg'] + '-' + role_variables['device_name']

	lsblk_cmd = "lsblk | grep %s | awk '{ print $7 }'" % expected_name 
	lsblk_buf = subprocess.check_output(lsblk_cmd, shell=True).replace('\n', '').split()

	# For device type disk: there should be a listing in lsblk but no mountpoint in the 7th columb
	# For device type lvm: there should be no listing at all in lsblk
	# Might have to fine tune this as this develops more and check on the device type again and parse buffer depending on that
	if len(lsblk_buf) is not 0:
		fail_reasons.append('Check failed as %s is still mounted in lsblk command' % expected_name)
		failed = True

	return failed

def test_absent_state(role_variables, results):
    '''Test driver for absent status: return False is no tests failed'''
    failed = False 

    if verify_fstab_info(role_variables, results['tests_failed']):
    	failed = True
    else:
    	results['num_successes'] += 1

    if verify_lsblk_mount(role_variables, results['tests_failed']):
    	failed = True
    else:
    	results['num_successes'] += 1

    # To-Do: hardcoded for now, find more elegant solution
    results['num_tests'] += 2

    return failed 

def test_present_state(role_variables, results):
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

    if verify_size(role_variables, results['tests_failed']):
    	failed = True 
    else:
    	results['num_successes'] += 1

    results['num_tests'] += 3

    return failed

def check_invalid_vars(role_variables, results):
	failed = False 

	if role_variables['device_type'] is 'disk' and role_variables['device_name'] is not None:
		results['tests_failed'].append('Check failed as the device type is disk, but device name is defined')
		failed = True 

	if role_variables['device_type'] is 'disk' and role_variables['lvm_vg'] is not None:
		results['tests_failed'].append('Check failed as the device type is disk, but lvm_vg name is defined')
		failed = True

	if len(role_variables['disks']) <= 0:
		results['tests_failed'].append('Check failed as the size of the specified disks is 0')
		failed = True

	return failed

def run_module():
    '''Setup and initialize all relevant ansible module data'''
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

    # Note: present status (default) is going to build up the specified device variables
    # Will need to change this at some point 
    if not check_invalid_vars(module.params, results['tests_failed']):
	    if (module.params['state'] is not None) and (module.params['state'] in 'absent'):
		    tests_failed = test_absent_state(module.params, results)
	    else:
	        tests_failed = test_present_state(module.params, results)

	    module.exit_json(**results)
	# else:
	# 	module.exit_json(msg="{}".format(results['tests_failed']))
 

def main():
    run_module()

if __name__ == '__main__':
    main()
