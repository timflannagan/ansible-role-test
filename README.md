Initial Testing Module
======

Runs an ansible playbook and verifies those results against available system information

To-Do:
======
1. Parse the test.yml file in tests directory
	- This is going to be problematic, and unnecessarily complicated
2. Finish creating all verification tests
3. Look into adding unit testing using pytest
4. Implement testing for size comparisons
5. Check LVM2_member in lsblk -fi against device_type 
6. Restruction some of the verification functions as they do the same thing

Current Problems:
=====
1. Is the organization of the playbook going to stay the same?
	- For instance, what's the last variable?
		* Could populate a dictionary that handles that by declaring defaults
2. Is this testing an entire test.yml file or pausing after each include_role test?
3. Parsing the test.yml file would be difficult
	- Could have a series of functions that verifies lsblk, /etc/fstab, blkid
		info against a test's expected results
			* Could pass a series of variables, then a dictionary of expected results
4. Figure out how to ssh onto bos.csb computer
5. Most of the function use an 'expected' parameter, which is a dictionary
	* This unfortunately will have to be hard-coded, if going in this direction 
