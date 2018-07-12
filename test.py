#!/usr/bin python

import subprocess
# Tests: verify that lsblk and /etc/fstab has similar mount point matches
# Use lsblk/blkid to check fs_type
# Verify LVM Setup using lvs, vgs, pvs 

def setup_git_repo():
	git_ret = subprocess.call('git clone https://github.com/dwlehman/linux-storage-role', shell=True)

	if git_ret:
		return True

	return False

def get_vgs():
	'''Return a list of used volume group names'''
	result = []

	try:
		vgs_cmd = subprocess.check_output("sudo vgs --no-headings | awk '{ print $1 }'", shell=True)
		vgs = vgs_cmd.split()

		for (counter, vg) in enumerate(vgs):
			# For debugging purposes atm
			print('VG_%d: %s' % (counter, vg))
			result.append(vg)
                
	except subprocess.CalledProcessError as e:
	    print('Exception from vgs subprocess command: ', e.output)
	    
	return result

def get_num_tests(test_file_path):
	'''Parse test_file_path parameter and return number of tests used in file'''
	with open(test_file_path, 'r') as test_file:
		line = test_file.read()
                num_tests = line.count('include_role')

	return num_tests

def run_tests(test_file_path):
	'''Driver for test framework'''
	num_successes = 0
	num_tests = get_num_tests(test_file_path)

	# Not used right now
	ansible_run_cmd = 'ansible-playbook -K tests/test.yml'

	# Not used right now
	vgs_list = get_vgs()

	# Call the ansible_run_cmd and verify results from expectations
	# If test is successful, increment number of successes, else pass
	# Improve by having better debugging; what test failed and why
	# Could do this with a dictionary 

	return num_successes, num_tests

def main():
<<<<<<< HEAD
=======
	# This is pretty messy
>>>>>>> 4bea77cc2e7e9efce18eb9228ab47e44a48ea4e4
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
