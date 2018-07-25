#! /usr/bin/python3

'''
- Info about role variables: https://github.com/dwlehman/linux-storage-role/tree/initial-docs
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils import facts
import subprocess
import math

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
    failed = False 
    implemented = False 

    if not implemented:
        fail_reasons.append('Check failed as verify_disk_mount is not implemented yet.')
        return True

    return failed

def verify_mount(role_variables, fail_reasons):
    '''Function executes a lsblk command and checks role variables against parsed lsblk output'''
    is_default = False
    failed = False

    if role_variables['fs_type'] is None:
        role_variables['fs_type'] = 'xfs'

    if role_variables['device_type'] is None:
        is_default = True 

        lsblk_cmd = "lsblk -fi | grep -w %s | awk '{ print $1, $2, $4 }'" % role_variables['device_name']
    else:
        lsblk_cmd = "lsblk -fi | grep -w %s | awk '{ print $1, $2, $4 }'" % role_variables['disks'][0]

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

    cat_cmd = "cat /etc/fstab | grep -w %s | awk '{ print $1, $2, $3 }'" % expected_name
    cat_buf = subprocess.check_output(cat_cmd, shell=True).replace('\n', '').split()

    if len(cat_buf) is not 3:
        fail_reasons.append('Check failed as cat command failed to return the correct number of fields: %s.' % cat_buf)
        return True

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

def verify_free_size_percentage(role_variables, fail_reasons):
    failed = False
    implemented = False

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
            fail_reasons.append('Check failed as the expected size does not match the actual size: %d -> %d' % (debug_value, total_space))
            failed = True

    else:
        fail_reasons.append('Check failed as user entered an empty disks list (not sure how to handle this atm.)')
        failed = True

    return failed

def verify_vg_size_percentage(role_variables, fail_reasons):
    failed = False

    lvs_cmd = "sudo lvs %s --units g | grep -w %s | awk '{ print $4 }'" % (role_variables['lvm_vg'], role_variables['device_name'])
    lvs_buf = subprocess.check_output(lvs_cmd, shell=True).replace('g', '')

    vgs_cmd = "sudo vgs %s --no-headings --units g| awk '{ print $1, $6, $7 }'" % role_variables['lvm_vg']
    vgs_buf = subprocess.check_output(vgs_cmd, shell=True).replace('g', '').split()

    if (len(lvs_buf) is not 1) or (len(vgs_buf) is not 3):
        fail_reasons.append('Check failed as vgs/pvs command did not return the required number of fields (verigy_vg_size_percentage).')
        return True

    if not role_variables['lvm_vg'] in vgs_buf[0]:
        fail_reasons.append('DEBUG: lvm name does not match the name pulled from the vgs command out in %VG.')
        return True

    total_size = float(vgs_buf[1].replace('g', ''))
    free_space = float(vgs_buf[2].replace('g', ''))
    actual_size = float(lvs_buf)
    expected_percentage = float(role_variables['size'].split('%')[0]) * 0.01

    expected_size = expected_percentage * total_size

    if expected_size != actual_size: 
        if free_space != 0.0:
            fail_reasons.append('Check failed as the expected size and actual size differ (%VG): %d / %d' % (expected_size, actual_size))
            failed = True

    return failed

def verify_pv_size_percentage(role_variables, fail_reasons):
    failed = False

    lvs_cmd = "sudo lvs --units g | grep -w %s | awk '{ print $4 }'" % role_variables['device_name']
    lvs_buf = subprocess.check_output(lvs_cmd, shell=True).replace('g', '')

    pvs_cmd = "sudo pvs --units g | grep -w %s | awk '{ print $5, $6 }'" % role_variables['lvm_vg']
    pvs_buf = subprocess.check_output(pvs_cmd, shell=True).replace('g', '').split()

    if len(pvs_buf) is not 2:
        fail_reasons.append('Check failed as the length of the pvs buffer is the required size in %PV.')
        return True 

    total_size = float(pvs_buf[0])
    free_space = float(pvs_buf[1])
    actual_size = float(lvs_buf.replace('g', ''))
    expected_percentage = float(role_variables['size'].split('%')[0]) * 0.01

    expected_size = total_size * expected_percentage

    if expected_size != actual_size:
        if free_space != 0.0:
            fail_reasons.append('Check failed as the expected size and actual size differ (%PV): %d -> %d' % (expected_size, actual_size))
            failed = True

    return failed

def verify_size_percentage(role_variables, fail_reasons):
    '''Function checks the size field key in role_variables dictionary and calls the corrrect helper function.'''
    failed = False 

    if 'FREE' in role_variables['size']:
        failed = verify_free_size_percentage(role_variables, fail_reasons)      
    elif 'VG' in role_variables['size']:
        failed = verify_vg_size_percentage(role_variables, fail_reasons)
    elif 'PVS' in role_variables['size']:
        failed = verify_pv_size_percentage(role_variables, fail_reasons)
    else:
        fail_reasons.append('Check failed as user must have inputted an incorrect format for size. [FREE|VG|PV]')
        failed = True

    return failed 

def verify_size_default(lvm_vg_name, fail_reasons):
    '''Verify that the VG specified in the lvm_vg_name variable has no space left in the vgs command output.'''
    failed = False 

    vgs_cmd = "sudo vgs | grep -w %s | awk '{ print $7 }'" % lvm_vg_name
    vgs_buf = subprocess.check_output(vgs_cmd, shell=True).split()

    if len(vgs_buf) is not 1:
        fail_reasons.append('Something was inputted wrong in the site.yml file, exiting: %s.' % vgs_buf)
        return True

    if not '0' in vgs_buf[0]:
        fail_reasons.append('Check failed as default size was used in lvm creation but there is still space in the vg leftover.')
        return True

    return failed

def verify_size_specified_value(lvm_vg_name, device_name, size, fail_reasons):
    '''Check if the variables listed in the parameter list match the info presented in lsblk command output.'''
    failed = False 

    expected_name = lvm_vg_name + '-' + device_name
    lsblk_cmd = "lsblk | grep -w %s | awk '{ print $4 }'" % expected_name
    lsblk_buf = subprocess.check_output(lsblk_cmd, shell=True).replace('|-', '').replace("'-", '').split()

    if len(lsblk_buf) is not 1:
        fail_reasons.append('lsblk/grep command failed to produce the single field in verify_size')
        return True 

    if 'gib' in size.lower():
        size = size.lower().replace('gib', 'g')

    if 'mib' in size.lower():
        size = size.lower().replace('mib', 'mb')

    if not size.lower() in lsblk_buf[0].lower():
        fail_reasons.append('Check failed as there are differing sizes in lsblk: %s -> %s' % (size, lsblk_buf[0]))
        failed = True

    return failed

def verify_size(role_variables, fail_reasons):
    '''Check if lvm device has correct size'''
    failed = False 

    if role_variables['device_type'] is not None and role_variables['device_type'] in 'disk':
        return False 

    if role_variables['size'] is None or role_variables['size'] in '100%FREE':
        failed = verify_size_default(role_variables['lvm_vg'], fail_reasons)
    elif '%' in role_variables['size']:
        failed = verify_size_percentage(role_variables, fail_reasons)       
    else:
        failed = verify_size_specified_value(role_variables['lvm_vg'], role_variables['device_name'], role_variables['size'], fail_reasons)

    return failed 

def verify_absent_fstab_info(role_variables, fail_reasons):
    '''Check the /etc/fstab info and make sure no disk/lvm device is listed there when state is specified as absent'''
    failed = False 

    if role_variables['device_type'] is not None and role_variables['disks'] in 'disk':
        expected_name = '/dev/' + role_variables['disks'][0]
    else:
        expected_name = '/dev/mapper/' + role_variables['lvm_vg'] + '-' + role_variables['device_name']

    cat_cmd = "cat /etc/fstab | grep -w %s | awk '{ print $1, $2, $3 }'" % expected_name
    cat_buf = subprocess.check_output(cat_cmd, shell=True).replace('\n', '').split()

    if len(cat_buf) is not 0:
        fail_reasons.append('Check failed as %s is still listed in the /etc/fstab file' % expected_name)
        failed = True

    return failed

def verify_absent_lsblk_mount(role_variables, fail_reasons):
    '''Check if corresponding device type is nonexistent in lsblk command output'''
    failed = False

    if role_variables['device_type'] is not None and role_variables['device_type'] in 'disk':
        expected_name = role_variables['disks'][0]
    else:
        expected_name = role_variables['lvm_vg'] + '-' + role_variables['device_name']

    lsblk_cmd = "lsblk | grep -w %s | awk '{ print $7 }'" % expected_name 
    lsblk_buf = subprocess.check_output(lsblk_cmd, shell=True).replace('\n', '').split()

    # For device type disk: there should be a listing in lsblk but no mountpoint in the 7th columb
    # For device type lvm: there should be no listing at all in lsblk
    if len(lsblk_buf) is not 0:
        fail_reasons.append('Check failed as %s is still mounted in lsblk command' % expected_name)
        failed = True

    return failed

def test_absent_state(role_variables, results):
    '''Test driver for absent status: return False is no tests failed'''
    failed = False 

    if verify_absent_fstab_info(role_variables, results['tests_failed']):
        failed = True
    else:
        results['num_successes'] += 1

    if verify_absent_lsblk_mount(role_variables, results['tests_failed']):
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

    if role_variables['device_type'] is 'disk' and len(role_variables['disks']) > 1:
        results['tests_failed'].append('Check failed as the device type is disk, but theres multiple disks in the list of specified disks.')

    if len(role_variables['disks']) <= 0:
        results['tests_failed'].append('Check failed as the size of the specified disks is 0')
        failed = True

    # Need to make sure that size is not None || get errorMsg
    if role_variables['size'] is not None and '+' in role_variables['size']:
        results['tests_failed'].append('Check failed as testing module does not support extending lvs')
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
    if check_invalid_vars(module.params, results['tests_failed']):
        module.exit_json(msg='Tests failed in the initial scanning of the parameters: {}'.format(results['tests_failed']))

    # Check the state variable to determine which state driver to use
    if (module.params['state'] is not None) and (module.params['state'] in 'absent'):
        tests_failed = test_absent_state(module.params, results)
    else:
        tests_failed = test_present_state(module.params, results)

    if not tests_failed:
        module.exit_json(**results)
    else:
        module.exit_json(msg='One or more tests have failed: {}'.format(results['tests_failed']))

def main():
    run_module()

if __name__ == '__main__':
    main()
