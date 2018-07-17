#! /usr/bin/python

'''
- Info about role variables: https://github.com/dwlehman/linux-storage-role/tree/initial-docs
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils import facts

# Seems like more overhead having to call the same subprocess command for different verification functions

# Both LVM and disk device types will have mounted file systems
def verify_fs_type(module_params):
    xfs_type = False
    lvm_device = False
    rval = False

    # Steps:
    # 1. Check whether device type is None (default is lvm)
    #    a. Default: Need to know device name, check against its fs type in /etc/fstab
    #    b. Other: Need to check the disks against its mounted fs type
    # 2. Check whether expected_fs_type is None (default is xfs)

    if module_params['device_type'] is not None:
        lsblk_cmd = "lsblk -fi | grep %s | awk '{ print $1, $2 }'" % module_params['device_name']
    else:
        # This is a stub atm
        lvm_device = True
        # lsblk_cmd = "lsblk -fi | grep %s | awk '{ print $1, $2 }'" % module_params['disks']

    lsblk_buf = subprocess.check_output(lsblk_cmd, shell=True)

    if not lvm_device:
        lsblk_buf = lsblk_buf.split()
    else:
        # We know this is an lvm device, so we need to be careful in parsing the input
        lsblk_buf = lsblk_buf.replace('|-', '').split()

        # Now we need to check if the file system type
        if module_params['fs_type'] is not None:
            if not module_params['device_name'] in lsblk_buf[0] or not module_params['fs_type'] in lsblk_buf[1]:
                # Eventually add some way to use error messages
                rval = False

        # lsblk_buf[0] = device_name, lsblk_buf[1] = file system type


    return True

def initialize_expected_results(module_params):
    fail_flag = False
    tests_failed = []
    num_successes = 0
    num_tests = 1

    if not verify_fs_type(module_params['fs_type']):
        tests_failed.append('Verify File System Type')
        fail_flag = True
    else:
        num_successes += 1

    return tests_failed, num_successes, num_tests

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
        lvm_vg              = dict(type='str')
    )
    # Will probably change as this module develops more
    results = dict(
        changed=False,
        num_tests=0,
        num_successes=0,
        tests_failed=[],
        fs_type=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # This is a debug check
    results['fs_type'] = module.params['fs_type']

    # This is pretty messy atm
    results['tests_failed'], results['num_successes'], results['num_tests'] = initialize_expected_results(module.params)

    if results['num_tests'] != 0 or results['num_successes'] != 0:
        module.exit_json(**results)
    else:
        module.fail_json(msg="Was unable to run any tests or initialize any return results")

def main():
    run_module()

if __name__ == '__main__':
    main()
