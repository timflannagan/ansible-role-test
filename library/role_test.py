#! /usr/bin/python

'''
- Info about role variables: https://github.com/dwlehman/linux-storage-role/tree/initial-docs
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils import facts

def initialize_expected_results(module_params):
    return [], 2, 2

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
        tests_failed=[]
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

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
