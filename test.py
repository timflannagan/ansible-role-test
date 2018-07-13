#!/usr/bin python

import subprocess
# Tests: verify that lsblk and /etc/fstab has similar mount point matches
# Use lsblk/blkid to check fs_type
# Verify LVM Setup using lvs, vgs, pvs

def get_vgs():
    '''Return a list of used volume group names'''
    result = []

    try:
        vgs_cmd = subprocess.check_output("sudo vgs --no-headings | awk '{ print $1 }'", shell=True)
        vgs = vgs_cmd.split()

        for (counter, vg) in enumerate(vgs):
            result.append(vg)

    # Might need to change this, look into subprocess exceptions
    except subprocess.CalledProcessError as e:
        print('Exception from vgs subprocess command: ', e.output)

    return result

def get_num_tests(test_file_path):
    '''Parse test_file_path parameter and return number of tests used in file'''
    with open(test_file_path, 'r') as test_file:
        lines = test_file.read()
        num_tests = lines.count('include_role')

    return num_tests

def verify_vgs(actual_vgs, expected):
    if expected['device_type'] == 'disk' and expected['lvm_vg'] == '':
        return True
    elif expected['lvm_vgs'] in actual_vgs:
        return True

    return False

def verify_mount(expected):
    lsblk_cmd = ("lsblk | grep %s | awk '{ print $1, $7 }'" % expected['device_name'])
    lsblk_buf = subprocess.check_output(lsblk_cmd, shell=True)
    lsblk_buf = lsblk_buf[6:].replace('\n', '')

    lsblk_buf = lsblk_buf.split()

    # Not entirely sure what is suppose to come first in the 'in' keyword
    if (not lsblk_buf[0] in expected['device_name']) or (not lsblk_buf[1] in expected['mount_point']):
        print('***Check failed with different mount info in lsblk command***')
        return False

    return True

def verify_fs_type(expected):
    blkid_cmd = ("blkid | grep %s | awk '{ print $3 }'" % expected['device_name'])
    blkid_buf = subprocess.check_output(blkid_cmd, shell=True)
    blkid_buf = blkid_buf[5:].replace('\n', '').replace('"', '')

    # This seems awkward to call subprocess on reading a file
    cat_cmd = ("cat /etc/fstab | grep %s | awk '{ print $1, $3 }'" % expected['device_name'])
    cat_buf = subprocess.check_output(cat_cmd, shell=True)
    cat_buf = cat_buf.split()

    # Look more into 'in' keyword when using strings
    if (not expected['device_name'] in cat_buf[0]) or (not expected['fs_type'] in cat_buf[1]):
        print('***Check failed with differing information in /etc/fstab file***')
        return False

    if not blkid_buf in expected['fs_type']:
        print('***Check failed with differing file system type in blkid***')
        return False

    return True

def run_tests(test_file_path):
    '''Driver for test framework'''
    num_successes = 0
    num_tests = get_num_tests(test_file_path)

    # Not used right now
    ansible_run_cmd = 'ansible-playbook -K tests/test.yml'

    # Not used right now
    vgs_list = get_vgs()
    test_list = []

    # Check if this is the most practical usage
    for test in range(num_tests):
        test_list.append({'device_type': 'lvm', 'device_name': None, 'disks': None, 'lvm_vg': None, 'mount_point': None, 'size': '100%', 'state': 'present', 'fs_type': 'xfs' })

    for (counter, test) in enumerate(test_list):
        fail = False
        # Not ready to test yet
        # if not verify_vgs('disk', vgs_list, ''):
        #     fail = True
        #     print('Test %d failed with volume groups' % counter)
        #
        # if not verify_mount('foo-test1', '/opt/test1/'):
        #     fail = True
        #     print('Test %d failed with mount points' % counter)
        #
        # if not verify_fs_type('foo-test1', 'ext'):
        #     fail = True
        #     print('Test %d failed with different file system types' % counter)
        #
        # if not fail:
        #     print('Test %d passed all tests' % counter)
        #     num_successes += 1

    # Call the ansible_run_cmd and verify results from expectations
    # If test is successful, increment number of successes, else pass
    # Improve by having better debugging; what test failed and why
    # Could do this with a dictionary
    return num_successes, num_tests

def main():
    locate_cmd = "locate -w linux-storage-role | awk 'NR==1 { print $1 }'"
    file_path = locate_buf + '/tests/test.yml'
    num_success, num_tests = run_tests(file_path)

    print('> Testing results: %d/%d total' % (num_success, num_tests))

if __name__ == '__main__':
    main()
