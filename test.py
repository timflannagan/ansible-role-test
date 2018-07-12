#!/usr/bin python

import subprocess
# Tests: verify that lsblk and /etc/fstab has similar mount point matches
# Use lsblk/blkid to check fs_type
# Verify LVM Setup using lvs, vgs, pvs 

def setup_git_repo():
	git_ret = subprocess.call('git clone -b task-flow https://github.com/dwlehman/linux-storage-role', shell=True)

	if git_ret:
		return True

	return False

def get_vgs():
	try:
		vgs_cmd = subprocess.check_output("sudo vgs --no-headings | awk '{ print $1 }'", shell=True)
		vgs = vgs_cmd.split()

		for (counter, vg) in enumerate(vgs):
			print('VG_%d: %s' % (counter, vg))
                
	except subprocess.CalledProcessError as e:
	    print('Exception from vgs subprocess command: ', e.output)
	    return 

def get_num_tests(test_file_path):
	with open(test_file_path, 'r') as test_file:
		line = test_file.read()
                num_tests = line.count('include_role')

	return num_tests

def run_tests(test_file_path):
	num_successes = 0
	num_tests = get_num_tests(test_file_path)

	run_cmd = 'ansible-playbook -K tests/test.yml'

	vgs_list = get_vgs()

	return num_successes, num_tests

def main():
        locate_cmd = "locate -w linux-storage-role | awk 'NR==1 { print $1 }'"
        locate_buf = subprocess.check_output(locate_cmd, shell=True)
        locate_buf = locate_buf.replace('\n', '')

        if not len(locate_buf):
                setup_git_repo()
                file_path = '~/linux-storage-role/tests/test.yml'

        file_path = locate_buf + '/tests/test.yml'
	num_success, num_tests = run_tests(file_path)

	print('> Testing results: %d/%d total' % (num_success, num_tests))

if __name__ == '__main__':
	main()
