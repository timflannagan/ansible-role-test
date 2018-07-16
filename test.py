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
    if expected['device_type'] == 'disk' and not expected['lvm_vg'] == '':
        print('Check failed with differing device types: %s -> %s' % (expected['device_type'], expected['lvm_vg']))
        return False
    elif expected['device_type'] != 'disk' and not expected['lvm_vg'] in actual_vgs:
        print('Check failed with the expected lvm_vg (%s) differing from a list of actual vgs' % expected['lvm_vg'])
        return False

    return True

def verify_mount(expected):
    disk_flag = False 
    rval = True

    if expected['device_type'] == 'disk':
        disk_flag = True

    if disk_flag:
        # This seems super awkward
        for disk in expected['disks']:
            lsblk_cmd = ("lsblk | grep %s | awk '{ print $1, $7 }'" % disk)
            lsblk_buf = subprocess.check_output(lsblk_cmd, shell=True)
            lsblk_buf = lsblk_buf.split()

            # Debug check: Something went wrong with expected input, delete later
            if not len(lsblk_buf[1]):
                print('Error in lsblk command: device type is disk but has no mounting point')
                rval = False

            if not expected['mount_point'] in lsblk_buf[1]:
                print('Check failed with disk drive having differing mounting locations')
                rval = False 
    else:
        lsblk_cmd = ("lsblk | grep %s | awk '{ print $1, $7 }'" % expected['device_name'])
        lsblk_buf = subprocess.check_output(lsblk_cmd, shell=True)
        lsblk_buf = lsblk_buf[6:].replace('\n', '')
        lsblk_buf = lsblk_buf.split()

        if not expected['device_name'] in lsblk_buf[0]:
            print('Check failed with different device names: %s -> %s' % (expected['device_name'], lsblk_buf[0]))
            rval = False

        if not expected['mount_point'] in lsblk_buf[1]:
            print('Check failed with different mount points: %s -> %s' % (expected['mount_point'], lsblk_buf[1]))
            rval = False

    return rval

def verify_fs_type(expected):   
    '''Test output from lsblk command and /etc/fstab file, against an expected dictionary of results'''
    disk_flag = False 
    rval = True

    if expected['device_type'] == 'disk':
        disk_flag = True 
        lsblk_cmd = ("lsblk -fi | grep %s | awk '{ print $2, $4 }'" % expected['mount_point'])
        cat_cmd = ("cat /etc/fstab | grep %s | awk '{ print $1, $3 }'" % expected['mount_point'])
    else:
        lsblk_cmd = ("lsblk -fi | grep %s | awk '{ print $1, $2, $4 }'" % expected['device_name'])
        cat_cmd = ("cat /etc/fstab | grep %s | awk '{ print $1, $3 }'" % expected['device_name'])

    lsblk_buf = subprocess.check_output(lsblk_cmd, shell=True)
    cat_buf = subprocess.check_output(cat_cmd, shell=True)

    lsblk_buf = lsblk_buf.split()
    cat_buf = cat_buf.split()

    if disk_flag:
        if not expected['fs_type'] in lsblk_buf[0]:
            print('Check failed with differing file system types: %s -> %s' % (expected['fs_type'], lsblk_buf[0]))
            rval = False
        # This is redundant with verify_mount, but keep for now
        if not expected['mount_point'] in lsblk_buf[1]:
            print('Check failed with differing mount points: %s -> %s' % (expected['mount_point'], lsblk_buf[1]))
            rval = False
    else:
        if (not expected['device_name'] in lsblk_buf[0]):
            print('Check failed with differing device names: %s -> %s' % (expected['device_name'], lsblk_buf[0][6:]))
            rval = False

        if (not expected['device_name'] in cat_buf[0]):
            print('Check failed with differing device names: %s -> %s' % (expected['device_name'], cat_buf[0]))
            rval = False 

        if (not expected['fs_type'] in cat_buf[1]):
            print('Check failed with differing fs types: %s -> %s' % (expected['fs_type'], cat_buf[1]))
            rval = False 

    return rval

def run_tests(test_file_path):
    '''Driver for test framework'''
    num_tests = get_num_tests(test_file_path)
    vgs_list = get_vgs()
    num_successes = 0
    test_list = []

    # Not used right now
    ansible_run_cmd = 'ansible-playbook -K tests/test.yml'

    # Hardcode for now to test loop further down 
    test_list.append({'device_type': 'lvm', 'device_name': 'test1', 
                      'disks': ['vdb'], 'lvm_vg': 'foo', 'mount_point': '/opt/test1', 
                      'size': '5g', 'fs_type': 'xfs', 'fs_label': '', 'state': 'present' })

    test_list.append({'device_type': 'lvm', 'device_name': 'test2', 'disks': ['vdb'], 
                      'lvm_vg': 'foo', 'mount_point': '/opt/test2', 'size': '100%', 
                      'fs_type': 'ext4', 'fs_label': '', 'state': 'present'})

    test_list.append({'device_type': 'disk', 'device_name': '', 'disks': ['vdc'], 
                      'lvm_vg': '', 'mount_point': '/opt/test3', 'size': '100%', 
                      'fs_type': 'xfs', 'fs_label': '', 'state': 'present'})

    # for test in range(num_tests):
    #     test_list.append({'device_type': 'lvm', 'device_name': None, 'disks': None, 'lvm_vg': None, 'mount_point': None, 'size': '100%', 'state': 'present', 'fs_type': 'xfs' })

    for (counter, test) in enumerate(test_list):
        fail = False

        print('>>> Testing test_%d' % (int(counter) + 1))
        if not verify_vgs(vgs_list, test_list[counter]):
            fail = True
        
        if not verify_mount(test_list[counter]):
            fail = True
        
        if not verify_fs_type(test_list[counter]):
            fail = True
        
        if not fail:
            print('Test %d passed all tests' % counter)
            num_successes += 1

    return num_successes, len(test_list)

def main():
    # Could assume the role path is located on root dir
    locate_cmd = "locate -w linux-storage-role | awk 'NR==1 { print $1 }'"
    locate_buf = subprocess.check_output(locate_cmd, shell=True)
    file_path = locate_buf.replace('\n', '') + '/tests/test.yml'

    num_success, num_tests = run_tests(file_path)
    print('> Testing results: %d/%d total' % (num_success, num_tests))

if __name__ == '__main__':
    main()
