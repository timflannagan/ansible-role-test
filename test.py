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

def get_num_tests():
	num_tests = 0

	with open('linux-storage-role/tests/test.yml', 'r') as test_file:
		lines = test_file.read()
		print('Line: ', lines)

	return num_tests

def run_tests():
	num_successes = 0
	num_tests = get_num_tests()

	run_cmd = 'ansible-playbook -K tests/test.yml'

	vgs_list = get_vgs()

	return num_successes, num_tests

def main():
	# if not setup_git_repo():
	# 	print('Was unable to setup git repo')
	# else:
	num_success, num_tests = run_tests()
	print('Return %d/%d' % (num_success, num_tests))

if __name__ == '__main__':
	main()